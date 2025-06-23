import argparse
import math
import os
import sys
from datetime import datetime
import itertools
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import zxcvbn
from tqdm import tqdm

class PasswordAnalyzer:
    @staticmethod
    def analyze_password(password, use_entropy=False):
        """Comprehensive password analysis using zxcvbn and entropy calculation"""
        result = zxcvbn.zxcvbn(password)
        analysis = {
            'password': password,
            'score': result['score'],
            'crack_time': result['crack_times_display']['offline_slow_hashing_1e4_per_second'],
            'warning': result['feedback'].get('warning', ''),
            'suggestions': result['feedback'].get('suggestions', []),
            'entropy': None
        }
        
        if use_entropy:
            # Calculate Shannon entropy
            char_set = set(password)
            pool_size = len(char_set)
            length = len(password)
            entropy = length * math.log2(pool_size) if pool_size > 0 else 0
            analysis['entropy'] = entropy
            analysis['strength'] = PasswordAnalyzer.entropy_to_strength(entropy)
        
        return analysis
    
    @staticmethod
    def entropy_to_strength(entropy):
        """Convert entropy value to strength category"""
        if entropy < 28: return "Very Weak"
        elif entropy < 36: return "Weak"
        elif entropy < 60: return "Moderate"
        elif entropy < 128: return "Strong"
        return "Very Strong"

class WordlistGenerator:
    L33T_MAP = {
        'a': ['4', '@'],
        'e': ['3'],
        'i': ['1', '!'],
        'o': ['0'],
        's': ['5', '$'],
        't': ['7', '+'],
        'b': ['8', '6'],
        'g': ['9'],
        'l': ['1'],
        'z': ['2']
    }
    
    COMMON_SUFFIXES = ['', '!', '@', '#', '$', '%', '^', '&', '*', '?', '123', '1234', 
                       '00', '01', '007', '1', '2', '3', '4', '5', '69', '88', '99', '000']
    
    COMMON_PREFIXES = ['', '!', '#', '$', '~', '^', '&', '*']
    
    KEYBOARD_WALKS = [
        'qwerty', 'asdfgh', 'zxcvbn', '123456', '1qaz2wsx', '1q2w3e4r', 
        'qazwsx', 'password', 'letmein', 'admin', 'welcome', 'monkey'
    ]
    
    def __init__(self, user_data):
        self.user_data = user_data
        self.base_words = self._generate_base_words()
        self.current_year = datetime.now().year
        self.generated_words = set()
    
    def _generate_base_words(self):
        """Create base words from user data"""
        words = set()
        
        # Add raw user data
        for value in self.user_data.values():
            if value:
                words.add(value.lower())
                words.add(value.capitalize())
        
        # Add combinations
        keys = [v for v in self.user_data.values() if v]
        if len(keys) > 1:
            for i in range(len(keys)):
                for j in range(i + 1, len(keys)):
                    words.add(keys[i] + keys[j])
                    words.add(keys[j] + keys[i])
                    words.add(keys[i].capitalize() + keys[j])
                    words.add(keys[i] + keys[j].capitalize())
                    words.add(keys[i] + '.' + keys[j])
                    words.add(keys[i] + '_' + keys[j])
        
        return list(words)
    
    def _leet_transform(self, word, max_subs=2):
        """Apply leet speak transformations with max substitutions"""
        if not max_subs or max_subs < 1:
            return [word]
        
        transformations = {word}
        char_list = list(word)
        leetable_positions = [i for i, c in enumerate(word) if c.lower() in self.L33T_MAP]
        
        # Apply all possible substitutions at once
        for k in range(1, min(max_subs, len(leetable_positions)) + 1):
            for positions in itertools.combinations(leetable_positions, k):
                for combo in itertools.product(*[self.L33T_MAP.get(char_list[pos].lower(), [char_list[pos]]) for pos in positions]):
                    new_word = char_list[:]
                    for idx, char in zip(positions, combo):
                        new_word[idx] = char
                    transformations.add(''.join(new_word))
        
        return list(transformations)
    
    def _generate_number_variations(self):
        """Generate common number sequences to append"""
        numbers = []
        
        # Current and recent years
        for year in range(self.current_year - 10, self.current_year + 5):
            numbers.append(str(year))
        
        # Common numeric patterns
        for i in range(0, 100):
            numbers.append(str(i).zfill(2))
        
        for i in [111, 123, 234, 345, 456, 567, 678, 789, 300, 999, 799, 100, 200]:
            numbers.append(str(i))
        
        return list(set(numbers))
    
    def generate_wordlist(self, output_file, max_leet_subs=1, include_common=True, include_keyboard=True):
        """Generate comprehensive wordlist and save to file"""
        number_variations = self._generate_number_variations()
        total_iterations = len(self.base_words) * (len(number_variations) + 1) * 2 * len(self.COMMON_SUFFIXES)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # Add keyboard walks if enabled
                if include_keyboard:
                    for walk in self.KEYBOARD_WALKS:
                        f.write(walk + '\n')
                
                # Process all base words
                for base_word in tqdm(self.base_words, desc="Generating wordlist", unit="base"):
                    # Original and case variants
                    variants = {base_word.lower(), base_word.capitalize()}
                    
                    # Leet transformations
                    leet_variants = set()
                    for variant in variants:
                        leet_variants.update(self._leet_transform(variant, max_leet_subs))
                    
                    # Combine with number variations and suffixes
                    all_combinations = set()
                    for word in leet_variants:
                        # Word without numbers
                        all_combinations.add(word)
                        
                        # Word with number suffixes
                        for num in number_variations:
                            all_combinations.add(word + num)
                        
                        # Word with number prefixes
                        for num in number_variations:
                            all_combinations.add(num + word)
                    
                    # Add common suffixes
                    final_words = set()
                    for word in all_combinations:
                        for suffix in self.COMMON_SUFFIXES:
                            final_words.add(word + suffix)
                    
                    # Write to file
                    for word in final_words:
                        if 4 <= len(word) <= 64:  # Practical length limits
                            f.write(word + '\n')
                
                # Add common passwords if enabled
                if include_common:
                    f.writelines(word + '\n' for word in self.KEYBOARD_WALKS)
        
        except Exception as e:
            raise RuntimeError(f"Wordlist generation failed: {str(e)}")
        
        return os.path.getsize(output_file)

class CLIInterface:
    @staticmethod
    def run():
        parser = argparse.ArgumentParser(description="Password Strength Analyzer & Wordlist Generator")
        subparsers = parser.add_subparsers(dest='command', required=True)
        
        # Analyze command
        analyze_parser = subparsers.add_parser('analyze', help='Analyze password strength')
        analyze_parser.add_argument('password', help='Password to analyze')
        analyze_parser.add_argument('--entropy', action='store_true', help='Include entropy calculation')
        
        # Generate command
        generate_parser = subparsers.add_parser('generate', help='Generate custom wordlist')
        generate_parser.add_argument('--output', required=True, help='Output file path')
        generate_parser.add_argument('--first', help='First name')
        generate_parser.add_argument('--last', help='Last name')
        generate_parser.add_argument('--nick', help='Nickname')
        generate_parser.add_argument('--birth', help='Birth year')
        generate_parser.add_argument('--pet', help='Pet name')
        generate_parser.add_argument('--company', help='Company name')
        generate_parser.add_argument('--max-leet', type=int, default=1, help='Max leet substitutions (0-3)')
        generate_parser.add_argument('--no-common', action='store_true', help='Exclude common passwords')
        generate_parser.add_argument('--no-keyboard', action='store_true', help='Exclude keyboard walks')
        
        args = parser.parse_args()
        
        if args.command == 'analyze':
            result = PasswordAnalyzer.analyze_password(args.password, args.entropy)
            CLIInterface.display_analysis(result)
        elif args.command == 'generate':
            user_data = {
                'first': args.first,
                'last': args.last,
                'nick': args.nick,
                'birth': args.birth,
                'pet': args.pet,
                'company': args.company
            }
            if not any(user_data.values()):
                print("Error: At least one user data field required for wordlist generation")
                sys.exit(1)
                
            generator = WordlistGenerator(user_data)
            try:
                size = generator.generate_wordlist(
                    args.output,
                    max_leet_subs=args.max_leet,
                    include_common=not args.no_common,
                    include_keyboard=not args.no_keyboard
                )
                print(f"Wordlist generated: {args.output} ({size/1024:.1f} KB)")
            except Exception as e:
                print(f"Error: {str(e)}")
                sys.exit(1)
    
    @staticmethod
    def display_analysis(result):
        print("\nPassword Strength Analysis")
        print("=" * 40)
        print(f"Password: {result['password']}")
        print(f"Strength Score: {result['score']}/4")
        print(f"Estimated Crack Time: {result['crack_time']}")
        
        if result['entropy'] is not None:
            print(f"Entropy: {result['entropy']:.2f} bits ({result['strength']})")
        
        if result['warning']:
            print(f"\nWarning: {result['warning']}")
        
        if result['suggestions']:
            print("\nSuggestions:")
            for suggestion in result['suggestions']:
                print(f"- {suggestion}")
        print("=" * 40)

class GUIInterface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Password Toolkit Pro")
        self.geometry("800x600")
        self.resizable(True, True)
        self.configure(bg="#2c3e50")
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#2c3e50')
        self.style.configure('TLabel', background='#2c3e50', foreground='#ecf0f1')
        self.style.configure('TButton', background='#3498db', foreground='#2c3e50')
        self.style.map('TButton', background=[('active', '#2980b9')])
        self.style.configure('TNotebook', background='#2c3e50')
        self.style.configure('TNotebook.Tab', background='#34495e', foreground='#ecf0f1')
        self.style.map('TNotebook.Tab', background=[('selected', '#3498db')])
        self.style.configure('TEntry', fieldbackground='#ecf0f1')
        self.style.configure('TCombobox', fieldbackground='#ecf0f1')
        
        # Create tabs
        self.notebook = ttk.Notebook(self)
        self.analyze_frame = ttk.Frame(self.notebook)
        self.generate_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analyze_frame, text='Password Analysis')
        self.notebook.add(self.generate_frame, text='Wordlist Generator')
        self.notebook.pack(expand=1, fill='both', padx=10, pady=10)
        
        # Build UI components
        self.create_analyze_tab()
        self.create_generate_tab()
        
        # Status bar
        self.status = tk.StringVar()
        self.status.set("Ready")
        status_bar = ttk.Label(self, textvariable=self.status, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_analyze_tab(self):
        frame = self.analyze_frame
        
        # Password entry
        ttk.Label(frame, text="Password to Analyze:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.password_entry = ttk.Entry(frame, width=40, show="•")
        self.password_entry.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        self.password_entry.focus()
        
        # Options
        self.entropy_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Calculate Entropy", variable=self.entropy_var).grid(
            row=1, column=1, padx=10, pady=5, sticky='w')
        
        # Analyze button
        analyze_btn = ttk.Button(frame, text="Analyze Password", command=self.analyze_password)
        analyze_btn.grid(row=2, column=0, columnspan=2, pady=15)
        
        # Results display
        self.results_text = scrolledtext.ScrolledText(frame, width=70, height=15, bg="#34495e", fg="#ecf0f1")
        self.results_text.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
        self.results_text.config(state=tk.DISABLED)
        
        # Configure grid weights
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(3, weight=1)
    
    def create_generate_tab(self):
        frame = self.generate_frame
        
        # User info fields
        fields = [
            ('first', 'First Name:'),
            ('last', 'Last Name:'),
            ('nick', 'Nickname:'),
            ('birth', 'Birth Year:'),
            ('pet', 'Pet\'s Name:'),
            ('company', 'Company:')
        ]
        
        self.user_vars = {}
        for i, (key, label) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=i, column=0, padx=10, pady=5, sticky='w')
            self.user_vars[key] = tk.StringVar()
            ttk.Entry(frame, textvariable=self.user_vars[key]).grid(
                row=i, column=1, padx=10, pady=5, sticky='ew')
        
        # Options
        ttk.Label(frame, text="Leet Substitutions:").grid(
            row=len(fields), column=0, padx=10, pady=5, sticky='w')
        self.leet_var = tk.IntVar(value=1)
        leet_combo = ttk.Combobox(frame, textvariable=self.leet_var, values=[0, 1, 2, 3], width=5)
        leet_combo.grid(row=len(fields), column=1, padx=10, pady=5, sticky='w')
        
        self.common_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Include Common Passwords", variable=self.common_var).grid(
            row=len(fields)+1, column=0, columnspan=2, padx=10, pady=5, sticky='w')
        
        self.keyboard_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Include Keyboard Walks", variable=self.keyboard_var).grid(
            row=len(fields)+2, column=0, columnspan=2, padx=10, pady=5, sticky='w')
        
        # File selection
        ttk.Label(frame, text="Output File:").grid(
            row=len(fields)+3, column=0, padx=10, pady=10, sticky='w')
        self.output_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.output_var).grid(
            row=len(fields)+3, column=1, padx=(0, 10), pady=10, sticky='ew')
        ttk.Button(frame, text="Browse...", command=self.browse_file).grid(
            row=len(fields)+3, column=2, padx=(0, 10), pady=10)
        
        # Generate button
        generate_btn = ttk.Button(frame, text="Generate Wordlist", command=self.generate_wordlist)
        generate_btn.grid(row=len(fields)+4, column=0, columnspan=3, pady=15)
        
        # Configure grid weights
        frame.columnconfigure(1, weight=1)
    
    def analyze_password(self):
        password = self.password_entry.get()
        if not password:
            messagebox.showerror("Error", "Please enter a password to analyze")
            return
        
        try:
            result = PasswordAnalyzer.analyze_password(password, self.entropy_var.get())
            self.display_results(result)
            self.status.set("Analysis completed")
        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")
    
    def display_results(self, result):
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        
        report = f"Password: {result['password']}\n"
        report += f"Strength Score: {result['score']}/4\n"
        report += f"Estimated Crack Time: {result['crack_time']}\n"
        
        if result['entropy'] is not None:
            report += f"Entropy: {result['entropy']:.2f} bits ({result['strength']})\n"
        
        if result['warning']:
            report += f"\nWarning: {result['warning']}\n"
        
        if result['suggestions']:
            report += "\nSuggestions:\n"
            for suggestion in result['suggestions']:
                report += f"- {suggestion}\n"
        
        self.results_text.insert(tk.END, report)
        self.results_text.config(state=tk.DISABLED)
    
    def browse_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.output_var.set(file_path)
    
    def generate_wordlist(self):
        user_data = {key: var.get().strip() for key, var in self.user_vars.items()}
        output_file = self.output_var.get()
        
        if not any(user_data.values()):
            messagebox.showerror("Error", "Please provide at least one piece of user information")
            return
        
        if not output_file:
            messagebox.showerror("Error", "Please specify an output file")
            return
        
        try:
            generator = WordlistGenerator(user_data)
            size = generator.generate_wordlist(
                output_file,
                max_leet_subs=self.leet_var.get(),
                include_common=self.common_var.get(),
                include_keyboard=self.keyboard_var.get()
            )
            self.status.set(f"Wordlist generated: {output_file} ({size/1024:.1f} KB)")
            messagebox.showinfo("Success", f"Wordlist generated successfully!\nSize: {size/1024:.1f} KB")
        except Exception as e:
            messagebox.showerror("Error", f"Wordlist generation failed: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        CLIInterface.run()
    else:
        app = GUIInterface()
        app.mainloop()
