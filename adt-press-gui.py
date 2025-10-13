#!/usr/bin/env python3
"""
ADT Press Configuration GUI
A simple, clean interface for editing config.yaml and running the pipeline
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import yaml
import subprocess
import os
import sys
from pathlib import Path
import threading

class ADTConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ADT Press Configuration")
        self.root.geometry("900x800")
        
        # Set native macOS appearance
        self.setup_style()
        
        # Config file path
        self.config_path = Path(__file__).parent / "config" / "config.yaml"
        self.config_data = {}
        
        # Create UI
        self.create_widgets()
        self.load_config()
        
    def setup_style(self):
        """Configure style for clean macOS look"""
        style = ttk.Style()
        style.theme_use('aqua')  # macOS native theme
        
    def create_widgets(self):
        """Create all UI widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Header
        header = ttk.Label(main_frame, text="ADT Press Configuration", 
                          font=('Helvetica Neue', 24, 'bold'))
        header.grid(row=0, column=0, pady=(0, 20), sticky=tk.W)
        
        # Notebook (tabbed interface)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create tabs
        self.create_basic_tab()
        self.create_advanced_tab()
        self.create_models_tab()
        self.create_output_tab()
        
        # Button frame
        button_frame = ttk.Frame(main_frame, padding="20 10 0 0")
        button_frame.grid(row=2, column=0, sticky=(tk.E))
        
        # Buttons
        save_btn = ttk.Button(button_frame, text="Save Config", command=self.save_config)
        save_btn.grid(row=0, column=0, padx=5)
        
        run_btn = ttk.Button(button_frame, text="Run Pipeline", command=self.run_pipeline,
                            style='Accent.TButton')
        run_btn.grid(row=0, column=1, padx=5)
        
    def create_basic_tab(self):
        """Create basic configuration tab"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="Basic Settings")
        
        # Make scrollable
        canvas = tk.Canvas(tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        
        # Fields
        fields = []
        
        # Label
        fields.append(self.create_field(scrollable_frame, len(fields), "Label:", "label", 
                                       "Unique identifier for this run"))
        
        # PDF Path
        pdf_frame = ttk.Frame(scrollable_frame)
        pdf_frame.grid(row=len(fields), column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        pdf_frame.columnconfigure(1, weight=1)
        
        ttk.Label(pdf_frame, text="PDF Path:", font=('Helvetica Neue', 12, 'bold')).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.pdf_path_var = tk.StringVar()
        pdf_entry = ttk.Entry(pdf_frame, textvariable=self.pdf_path_var, width=50)
        pdf_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        browse_btn = ttk.Button(pdf_frame, text="Browse...", 
                               command=lambda: self.browse_file(self.pdf_path_var))
        browse_btn.grid(row=0, column=2, padx=5)
        fields.append(('pdf_path', self.pdf_path_var))
        
        # Languages
        fields.append(self.create_field(scrollable_frame, len(fields), "Input Language:", 
                                       "input_language", "Source language (e.g., es, en, fi)"))
        fields.append(self.create_field(scrollable_frame, len(fields), "Plate Language:", 
                                       "plate_language", "Language for plate extraction"))
        fields.append(self.create_field(scrollable_frame, len(fields), "Output Languages:", 
                                       "output_languages", "Comma-separated (e.g., es, en, fi)"))
        
        # Page Range
        range_frame = ttk.LabelFrame(scrollable_frame, text="Page Range", padding="10")
        range_frame.grid(row=len(fields), column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        range_frame.columnconfigure(1, weight=1)
        range_frame.columnconfigure(3, weight=1)
        
        ttk.Label(range_frame, text="Start:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.page_start_var = tk.StringVar()
        ttk.Entry(range_frame, textvariable=self.page_start_var, width=10).grid(
            row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(range_frame, text="End:").grid(row=0, column=2, sticky=tk.W, padx=15)
        self.page_end_var = tk.StringVar()
        ttk.Entry(range_frame, textvariable=self.page_end_var, width=10).grid(
            row=0, column=3, sticky=tk.W, padx=5)
        
        fields.append(('page_range.start', self.page_start_var))
        fields.append(('page_range.end', self.page_end_var))
        
        self.basic_fields = dict(fields)
        
    def create_advanced_tab(self):
        """Create advanced settings tab"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="Advanced")
        
        canvas = tk.Canvas(tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        
        fields = []
        
        # Strategies
        strategies_frame = ttk.LabelFrame(scrollable_frame, text="Processing Strategies", padding="15")
        strategies_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        strategies_frame.columnconfigure(1, weight=1)
        
        row = 0
        self.crop_strategy_var = tk.StringVar()
        ttk.Label(strategies_frame, text="Crop Strategy:").grid(row=row, column=0, sticky=tk.W, pady=5)
        crop_combo = ttk.Combobox(strategies_frame, textvariable=self.crop_strategy_var, 
                                 values=['llm', 'none'], width=20)
        crop_combo.grid(row=row, column=1, sticky=tk.W, padx=10)
        fields.append(('crop_strategy', self.crop_strategy_var))
        row += 1
        
        self.glossary_strategy_var = tk.StringVar()
        ttk.Label(strategies_frame, text="Glossary Strategy:").grid(row=row, column=0, sticky=tk.W, pady=5)
        glossary_combo = ttk.Combobox(strategies_frame, textvariable=self.glossary_strategy_var,
                                     values=['llm', 'none'], width=20)
        glossary_combo.grid(row=row, column=1, sticky=tk.W, padx=10)
        fields.append(('glossary_strategy', self.glossary_strategy_var))
        row += 1
        
        self.explanation_strategy_var = tk.StringVar()
        ttk.Label(strategies_frame, text="Explanation Strategy:").grid(row=row, column=0, sticky=tk.W, pady=5)
        exp_combo = ttk.Combobox(strategies_frame, textvariable=self.explanation_strategy_var,
                                values=['llm', 'none'], width=20)
        exp_combo.grid(row=row, column=1, sticky=tk.W, padx=10)
        fields.append(('explanation_strategy', self.explanation_strategy_var))
        row += 1
        
        self.easy_read_strategy_var = tk.StringVar()
        ttk.Label(strategies_frame, text="Easy Read Strategy:").grid(row=row, column=0, sticky=tk.W, pady=5)
        easy_combo = ttk.Combobox(strategies_frame, textvariable=self.easy_read_strategy_var,
                                 values=['llm', 'none'], width=20)
        easy_combo.grid(row=row, column=1, sticky=tk.W, padx=10)
        fields.append(('easy_read_strategy', self.easy_read_strategy_var))
        row += 1
        
        self.caption_strategy_var = tk.StringVar()
        ttk.Label(strategies_frame, text="Caption Strategy:").grid(row=row, column=0, sticky=tk.W, pady=5)
        caption_combo = ttk.Combobox(strategies_frame, textvariable=self.caption_strategy_var,
                                    values=['llm', 'none'], width=20)
        caption_combo.grid(row=row, column=1, sticky=tk.W, padx=10)
        fields.append(('caption_strategy', self.caption_strategy_var))
        row += 1
        
        self.speech_strategy_var = tk.StringVar()
        ttk.Label(strategies_frame, text="Speech Strategy:").grid(row=row, column=0, sticky=tk.W, pady=5)
        speech_combo = ttk.Combobox(strategies_frame, textvariable=self.speech_strategy_var,
                                   values=['tts', 'none'], width=20)
        speech_combo.grid(row=row, column=1, sticky=tk.W, padx=10)
        fields.append(('speech_strategy', self.speech_strategy_var))
        
        # Other options
        options_frame = ttk.LabelFrame(scrollable_frame, text="Other Options", padding="15")
        options_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.clear_cache_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Clear Cache", 
                       variable=self.clear_cache_var).grid(row=0, column=0, sticky=tk.W, pady=5)
        fields.append(('clear_cache', self.clear_cache_var))
        
        self.advanced_fields = dict(fields)
        
    def create_models_tab(self):
        """Create models configuration tab"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="Models")
        
        ttk.Label(tab, text="Default Model:", font=('Helvetica Neue', 12, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=10)
        
        self.default_model_var = tk.StringVar()
        model_combo = ttk.Combobox(tab, textvariable=self.default_model_var,
                                  values=['gpt-4o', 'gpt-4o-mini', 'gpt-5', 'gpt-4-turbo'],
                                  width=30)
        model_combo.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        info = ttk.Label(tab, text="This model will be used for all prompts unless overridden.",
                        foreground='gray')
        info.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 20))
        
        self.models_fields = {'default_model': self.default_model_var}
        
    def create_output_tab(self):
        """Create output/console tab"""
        tab = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(tab, text="Output")
        
        ttk.Label(tab, text="Pipeline Output:", font=('Helvetica Neue', 12, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        self.output_text = scrolledtext.ScrolledText(tab, wrap=tk.WORD, width=80, height=30,
                                                     font=('Monaco', 10))
        self.output_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        
    def create_field(self, parent, row, label_text, key, tooltip=""):
        """Helper to create a labeled entry field"""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        frame.columnconfigure(1, weight=1)
        
        label = ttk.Label(frame, text=label_text, font=('Helvetica Neue', 12, 'bold'))
        label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=var, width=50)
        entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        if tooltip:
            tip = ttk.Label(frame, text=tooltip, foreground='gray', font=('Helvetica Neue', 10))
            tip.grid(row=1, column=1, sticky=tk.W, pady=(2, 0))
        
        return (key, var)
    
    def browse_file(self, var):
        """Open file browser for PDF selection"""
        filename = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialdir=str(Path(__file__).parent / "assets")
        )
        if filename:
            var.set(filename)
    
    def load_config(self):
        """Load config from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config_data = yaml.safe_load(f)
            
            # Populate basic fields
            for key, var in self.basic_fields.items():
                if '.' in key:
                    # Handle nested keys like page_range.start
                    parts = key.split('.')
                    value = self.config_data.get(parts[0], {}).get(parts[1], '')
                elif key == 'output_languages':
                    value = ', '.join(self.config_data.get(key, []))
                else:
                    value = self.config_data.get(key, '')
                var.set(str(value))
            
            # Populate advanced fields
            for key, var in self.advanced_fields.items():
                value = self.config_data.get(key, '')
                if isinstance(var, tk.BooleanVar):
                    var.set(bool(value))
                else:
                    var.set(str(value))
            
            # Populate models
            for key, var in self.models_fields.items():
                var.set(self.config_data.get(key, ''))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config:\n{str(e)}")
    
    def save_config(self):
        """Save config to YAML file"""
        try:
            # Update config data
            for key, var in self.basic_fields.items():
                if '.' in key:
                    parts = key.split('.')
                    if parts[0] not in self.config_data:
                        self.config_data[parts[0]] = {}
                    try:
                        self.config_data[parts[0]][parts[1]] = int(var.get())
                    except ValueError:
                        self.config_data[parts[0]][parts[1]] = var.get()
                elif key == 'output_languages':
                    langs = [lang.strip() for lang in var.get().split(',')]
                    self.config_data[key] = langs
                else:
                    self.config_data[key] = var.get()
            
            for key, var in self.advanced_fields.items():
                if isinstance(var, tk.BooleanVar):
                    self.config_data[key] = var.get()
                else:
                    self.config_data[key] = var.get()
            
            for key, var in self.models_fields.items():
                self.config_data[key] = var.get()
            
            # Write to file
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, sort_keys=False)
            
            messagebox.showinfo("Success", "Configuration saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config:\n{str(e)}")
    
    def run_pipeline(self):
        """Run the ADT pipeline"""
        # Save config first
        self.save_config()
        
        # Switch to output tab
        self.notebook.select(3)
        
        # Clear output
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "Starting pipeline...\n")
        self.output_text.insert(tk.END, f"Label: {self.basic_fields['label'].get()}\n")
        self.output_text.insert(tk.END, f"PDF: {self.basic_fields['pdf_path'].get()}\n")
        self.output_text.insert(tk.END, "-" * 80 + "\n\n")
        
        # Run in separate thread to not freeze GUI
        thread = threading.Thread(target=self._run_pipeline_thread, daemon=True)
        thread.start()
    
    def _run_pipeline_thread(self):
        """Thread function to run pipeline"""
        try:
            # Build command
            label = self.basic_fields['label'].get()
            pdf_path = self.basic_fields['pdf_path'].get()
            
            cmd = ['uv', 'run', 'python', 'adt-press.py', 
                   f'label={label}', f'pdf_path={pdf_path}']
            
            # Run process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=Path(__file__).parent
            )
            
            # Stream output
            for line in process.stdout:
                self.output_text.insert(tk.END, line)
                self.output_text.see(tk.END)
                self.output_text.update()
            
            process.wait()
            
            if process.returncode == 0:
                self.output_text.insert(tk.END, "\n" + "=" * 80 + "\n")
                self.output_text.insert(tk.END, "Pipeline completed successfully!\n")
                self.output_text.insert(tk.END, "=" * 80 + "\n")
            else:
                self.output_text.insert(tk.END, "\n" + "=" * 80 + "\n")
                self.output_text.insert(tk.END, f"Pipeline failed with exit code {process.returncode}\n")
                self.output_text.insert(tk.END, "=" * 80 + "\n")
                
        except Exception as e:
            self.output_text.insert(tk.END, f"\nError running pipeline: {str(e)}\n")

def main():
    root = tk.Tk()
    app = ADTConfigGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
