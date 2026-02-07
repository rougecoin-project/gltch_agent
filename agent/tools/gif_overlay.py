"""
GLTCH GIF Overlay
Floating borderless window that pops up in the corner with a GIF,
stays for a few seconds, then fades away. Cyberpunk style.
Runs in a separate thread so it doesn't block the terminal.
"""

import os
import sys
import threading
import time
from typing import Optional


def _show_gif_overlay(gif_path: str, duration: int = 6, position: str = "bottom-right"):
    """
    Show a floating GIF overlay using tkinter.
    Runs in its own thread with its own event loop.
    
    Args:
        gif_path: Path to the GIF file
        duration: How long to show (seconds)
        position: Where to pop up (bottom-right, bottom-left, top-right, top-left)
    """
    try:
        import tkinter as tk
        from PIL import Image, ImageTk
    except ImportError:
        # Fallback: try to open with system viewer
        _fallback_open(gif_path)
        return
    
    try:
        root = tk.Tk()
        root.withdraw()  # Hide main window first
        
        # Create floating overlay
        overlay = tk.Toplevel(root)
        overlay.overrideredirect(True)  # No title bar, no borders
        overlay.attributes("-topmost", True)  # Always on top
        
        # Try transparency (Windows)
        try:
            overlay.attributes("-transparentcolor", "#000001")
            bg_color = "#000001"
        except Exception:
            bg_color = "#0a0a12"  # Fallback dark bg
        
        overlay.configure(bg=bg_color)
        
        # Load GIF
        img = Image.open(gif_path)
        
        # Resize to reasonable overlay size (max 280px wide)
        max_size = 280
        ratio = min(max_size / img.width, max_size / img.height)
        if ratio < 1:
            new_w = int(img.width * ratio)
            new_h = int(img.height * ratio)
        else:
            new_w, new_h = img.width, img.height
        
        # Add padding for border effect
        pad = 4
        window_w = new_w + pad * 2
        window_h = new_h + pad * 2
        
        # Position on screen
        screen_w = overlay.winfo_screenwidth()
        screen_h = overlay.winfo_screenheight()
        margin = 20
        
        positions = {
            "bottom-right": (screen_w - window_w - margin, screen_h - window_h - margin - 48),
            "bottom-left": (margin, screen_h - window_h - margin - 48),
            "top-right": (screen_w - window_w - margin, margin),
            "top-left": (margin, margin)
        }
        
        x, y = positions.get(position, positions["bottom-right"])
        overlay.geometry(f"{window_w}x{window_h}+{x}+{y}")
        
        # Create border frame (purple glow effect)
        border_frame = tk.Frame(overlay, bg="#a855f7", padx=2, pady=2)
        border_frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        inner_frame = tk.Frame(border_frame, bg="#0a0a12")
        inner_frame.pack(fill="both", expand=True)
        
        # Display label
        label = tk.Label(inner_frame, bg="#0a0a12", borderwidth=0)
        label.pack()
        
        # Extract frames for animation
        frames = []
        frame_delays = []
        try:
            frame_idx = 0
            while True:
                img.seek(frame_idx)
                frame = img.copy().resize((new_w, new_h), Image.Resampling.LANCZOS)
                tk_frame = ImageTk.PhotoImage(frame)
                frames.append(tk_frame)
                # Get frame duration (default 100ms)
                delay = img.info.get("duration", 100)
                frame_delays.append(max(delay, 30))  # Min 30ms
                frame_idx += 1
        except EOFError:
            pass
        
        if not frames:
            # Static image fallback
            img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img_resized)
            label.configure(image=tk_img)
            label.image = tk_img
        
        # Animation state
        current_frame = [0]
        start_time = [time.time()]
        
        def animate():
            if time.time() - start_time[0] > duration:
                # Fade out effect - just close
                try:
                    overlay.destroy()
                    root.destroy()
                except Exception:
                    pass
                return
            
            if frames:
                idx = current_frame[0] % len(frames)
                label.configure(image=frames[idx])
                label.image = frames[idx]
                current_frame[0] += 1
                delay = frame_delays[idx] if idx < len(frame_delays) else 100
                overlay.after(delay, animate)
        
        # Make it clickable to dismiss
        def dismiss(event=None):
            try:
                overlay.destroy()
                root.destroy()
            except Exception:
                pass
        
        overlay.bind("<Button-1>", dismiss)
        label.bind("<Button-1>", dismiss)
        
        # Show with slide-in effect
        overlay.deiconify()
        
        # Start animation
        if frames:
            animate()
        else:
            # Static: auto-close after duration
            overlay.after(duration * 1000, dismiss)
        
        # Run the event loop
        root.mainloop()
        
    except Exception as e:
        # If overlay fails, fall back to system viewer
        _fallback_open(gif_path)


def _fallback_open(gif_path: str):
    """Fallback: open with system default viewer."""
    import subprocess
    
    try:
        if sys.platform == 'win32':
            os.startfile(gif_path)
        elif sys.platform.startswith('linux'):
            # Check for WSL
            is_wsl = False
            try:
                with open('/proc/version', 'r') as f:
                    if 'microsoft' in f.read().lower():
                        is_wsl = True
            except Exception:
                pass
            
            if is_wsl:
                import shutil
                if shutil.which('wslview'):
                    subprocess.Popen(['wslview', gif_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif shutil.which('cmd.exe'):
                    wsl_path = subprocess.run(['wslpath', '-w', gif_path], capture_output=True, text=True).stdout.strip()
                    if wsl_path:
                        subprocess.Popen(['cmd.exe', '/c', 'start', '', wsl_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(['xdg-open', gif_path], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', gif_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def show_gif(gif_path: str, duration: int = 6, position: str = "bottom-right"):
    """
    Show a GIF overlay in a non-blocking way.
    Launches the overlay in a separate thread.
    
    Args:
        gif_path: Path to the GIF file
        duration: How long to show (seconds)
        position: Where to show (bottom-right, bottom-left, top-right, top-left)
    """
    if not os.path.exists(gif_path):
        return
    
    # Run in separate thread so terminal isn't blocked
    thread = threading.Thread(
        target=_show_gif_overlay,
        args=(gif_path, duration, position),
        daemon=True
    )
    thread.start()


# Quick test
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        show_gif(sys.argv[1], duration=5)
        # Keep main thread alive while overlay shows
        time.sleep(6)
    else:
        print("Usage: python gif_overlay.py <gif_path>")
