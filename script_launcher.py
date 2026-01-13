"""
Script Launcher GUI Application

Provides a graphical user interface with clickable buttons to easily run
important scripts for the Telegram Interview Bot project.

Features:
    - One-click script execution
    - Real-time output display
    - Confirmation dialogs for destructive operations
    - Cross-platform support (Windows/Linux/Mac)
"""

import sys
import os
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from config import (
    BASE_DIR,
    WINDOW_TITLE,
    WINDOW_SIZE,
    FONT_TITLE,
    FONT_DESCRIPTION,
    FONT_OUTPUT,
    OUTPUT_HEIGHT,
)

# Change to script directory for relative path resolution
os.chdir(BASE_DIR)


# ============================================================================
# SCRIPT DEFINITIONS
# ============================================================================

def get_script_definitions() -> List[Dict]:
    """
    Returns a list of script definitions with metadata.
    
    Each script dictionary contains:
        - name: Display name for the button
        - file: Script filename
        - description: Help text shown below the button
        - confirm: Whether to show confirmation dialog
        - confirm_msg: Confirmation message text
        - args: Additional command-line arguments (optional)
        - is_batch: Whether this is a Windows batch file
        - is_shell: Whether this is a Unix shell script
    
    Returns:
        List of script definition dictionaries
    """
    scripts = [
        {
            "name": "Recreate Database",
            "file": "recreate_database.py",
            "description": "Delete and recreate database with correct schema",
            "confirm": True,
            "confirm_msg": (
                "This will DELETE the entire database and recreate it.\n\n"
                "All data will be lost. Continue?"
            ),
        },
        {
            "name": "Reset Database",
            "file": "reset_database.py",
            "description": "Clear all interview data from database",
            "confirm": True,
            "confirm_msg": (
                "This will delete ALL interview data.\n\n"
                "Candidates and responses will be removed. Continue?"
            ),
            "args": ["--yes"],
        },
        {
            "name": "Fix Database",
            "file": "fix_database.py",
            "description": "Fix schema and clear all data",
            "confirm": True,
            "confirm_msg": (
                "This will fix the database schema and clear all data.\n\n"
                "All data will be lost. Continue?"
            ),
        },
        {
            "name": "Check Database",
            "file": "check_database.py",
            "description": "Check database status and contents",
            "confirm": False,
        },
        {
            "name": "Stop Bot",
            "file": "stop_bot.bat" if sys.platform == "win32" else "stop_bot.sh",
            "description": "Stop running bot processes",
            "confirm": False,
            "is_batch": sys.platform == "win32",
            "is_shell": sys.platform != "win32",
        },
    ]
    
    return scripts


# ============================================================================
# SCRIPT LAUNCHER GUI CLASS
# ============================================================================

class ScriptLauncher:
    """
    Main GUI application for launching scripts.
    
    Provides a window with buttons for each available script, an output
    area to display script results, and handles script execution in
    background threads to keep the UI responsive.
    """
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the script launcher GUI.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.buttons: Dict[str, ttk.Button] = {}
        self.scripts = get_script_definitions()
        
        self._setup_window()
        self._setup_ui()
        self._show_welcome_message()
    
    def _setup_window(self) -> None:
        """Configure the main window settings."""
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        
        # Configure window grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Set theme
        style = ttk.Style()
        style.theme_use('clam')
    
    def _setup_ui(self) -> None:
        """Create and arrange all UI components."""
        # Main container frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title label
        title_label = ttk.Label(
            main_frame,
            text="Script Launcher",
            font=FONT_TITLE
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Script buttons frame
        self._create_buttons_frame(main_frame)
        
        # Output frame
        self._create_output_frame(main_frame)
        
        # Clear output button
        self._create_clear_button(main_frame)
    
    def _create_buttons_frame(self, parent: ttk.Frame) -> None:
        """Create the frame containing script buttons."""
        buttons_frame = ttk.LabelFrame(
            parent,
            text="Available Scripts",
            padding="10"
        )
        buttons_frame.grid(
            row=1,
            column=0,
            sticky=(tk.W, tk.E, tk.N, tk.S),
            pady=(0, 10)
        )
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        
        # Create buttons in a 2-column grid
        row = 0
        col = 0
        
        for script in self.scripts:
            btn_frame = ttk.Frame(buttons_frame)
            btn_frame.grid(
                row=row,
                column=col,
                padx=5,
                pady=5,
                sticky=(tk.W, tk.E)
            )
            
            # Create button
            btn = ttk.Button(
                btn_frame,
                text=script["name"],
                command=lambda s=script: self.run_script(s),
                width=25
            )
            btn.pack(fill=tk.X)
            
            # Create description label
            desc_label = ttk.Label(
                btn_frame,
                text=script["description"],
                font=FONT_DESCRIPTION,
                foreground='gray'
            )
            desc_label.pack(fill=tk.X, pady=(2, 0))
            
            # Store button reference
            self.buttons[script["file"]] = btn
            
            # Move to next grid position
            col = (col + 1) % 2
            if col == 0:
                row += 1
    
    def _create_output_frame(self, parent: ttk.Frame) -> None:
        """Create the output text area frame."""
        output_frame = ttk.LabelFrame(
            parent,
            text="Output",
            padding="10"
        )
        output_frame.grid(
            row=2,
            column=0,
            sticky=(tk.W, tk.E, tk.N, tk.S)
        )
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        # Scrolled text widget for output
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            height=OUTPUT_HEIGHT,
            font=FONT_OUTPUT
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_clear_button(self, parent: ttk.Frame) -> None:
        """Create the clear output button."""
        clear_btn = ttk.Button(
            parent,
            text="Clear Output",
            command=self.clear_output
        )
        clear_btn.grid(row=3, column=0, pady=(10, 0))
    
    def _show_welcome_message(self) -> None:
        """Display welcome message in the output area."""
        self.append_output("Script Launcher Ready!\n")
        self.append_output("Select a script from the buttons above to run it.\n")
        self.append_output("-" * 50 + "\n")
    
    # ========================================================================
    # OUTPUT METHODS
    # ========================================================================
    
    def append_output(self, text: str) -> None:
        """
        Append text to the output area.
        
        Args:
            text: Text to append
        """
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_output(self) -> None:
        """Clear all text from the output area."""
        self.output_text.delete(1.0, tk.END)
    
    # ========================================================================
    # SCRIPT EXECUTION METHODS
    # ========================================================================
    
    def run_script(self, script: Dict) -> None:
        """
        Run a script in a separate thread (non-blocking).
        
        Args:
            script: Script definition dictionary
        """
        # Validate script file exists
        script_path = BASE_DIR / script["file"]
        if not script_path.exists():
            messagebox.showerror(
                "File Not Found",
                f"Script file not found:\n{script_path}"
            )
            return
        
        # Show confirmation dialog if required
        if script.get("confirm", False):
            if not messagebox.askyesno(
                "Confirm Action",
                script.get("confirm_msg", "Continue?")
            ):
                return
        
        # Disable button during execution
        if script["file"] in self.buttons:
            self.buttons[script["file"]].config(state="disabled")
        
        # Execute script in background thread
        thread = threading.Thread(
            target=self._execute_script,
            args=(script,),
            daemon=True
        )
        thread.start()
    
    def _execute_script(self, script: Dict) -> None:
        """
        Execute a script and capture its output.
        
        This method runs in a separate thread to avoid blocking the UI.
        
        Args:
            script: Script definition dictionary
        """
        script_path = BASE_DIR / script["file"]
        
        # Print header
        self.append_output(f"\n{'='*50}\n")
        self.append_output(f"Running: {script['name']}\n")
        self.append_output(f"File: {script['file']}\n")
        self.append_output(f"{'='*50}\n\n")
        
        try:
            # Build command based on script type
            cmd = self._build_command(script, script_path)
            
            # Execute script
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(BASE_DIR)
            )
            
            # Stream output in real-time
            for line in process.stdout:
                self.append_output(line)
            
            # Wait for completion
            process.wait()
            
            # Show completion status
            if process.returncode == 0:
                self.append_output(
                    f"\n✓ Script completed successfully "
                    f"(exit code: {process.returncode})\n"
                )
            else:
                self.append_output(
                    f"\n✗ Script exited with code: {process.returncode}\n"
                )
        
        except FileNotFoundError as e:
            error_msg = self._format_file_not_found_error(script, e)
            self.append_output(error_msg)
            messagebox.showerror("Execution Error", error_msg)
        
        except Exception as e:
            error_msg = f"Error running script:\n{e}\n"
            self.append_output(error_msg)
            messagebox.showerror("Execution Error", error_msg)
        
        finally:
            # Re-enable button
            if script["file"] in self.buttons:
                self.buttons[script["file"]].config(state="normal")
            
            self.append_output(f"\n{'='*50}\n\n")
    
    def _build_command(self, script: Dict, script_path: Path) -> List[str]:
        """
        Build the command list for executing a script.
        
        Args:
            script: Script definition dictionary
            script_path: Path to the script file
            
        Returns:
            List of command arguments
        """
        # Windows batch file
        if script.get("is_batch", False):
            return ["cmd.exe", "/c", str(script_path)]
        
        # Unix shell script
        elif script.get("is_shell", False):
            return ["bash", str(script_path)]
        
        # Python script
        else:
            cmd = [sys.executable, str(script_path)]
            if "args" in script:
                cmd.extend(script["args"])
            return cmd
    
    def _format_file_not_found_error(
        self,
        script: Dict,
        error: Exception
    ) -> str:
        """
        Format a helpful error message for file not found errors.
        
        Args:
            script: Script definition dictionary
            error: The FileNotFoundError exception
            
        Returns:
            Formatted error message string
        """
        error_msg = f"Error: Command not found.\n{error}\n"
        
        if script.get("is_shell", False) and sys.platform == "win32":
            error_msg += (
                "\nNote: Shell scripts require Bash "
                "(Git Bash or WSL).\n"
            )
        elif script.get("is_batch", False):
            error_msg += (
                "\nNote: Batch files require cmd.exe (Windows).\n"
            )
        
        return error_msg


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main() -> None:
    """Main entry point for the script launcher application."""
    root = tk.Tk()
    app = ScriptLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
