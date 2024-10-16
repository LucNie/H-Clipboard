import tkinter as tk
import pyperclip
from PIL import Image, ImageTk, ImageGrab
import io
import tempfile
import hashlib
import win32clipboard
from win32con import CF_DIB

class ClipboardHistoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Historique du Presse-papier")

        # Listes pour stocker l'historique du presse-papier (textes et images)
        self.text_history = []
        self.image_history = []
        self.image_hashes = set()  # Ensemble pour stocker les hachages d'images

        # Créer des listes dans l'IHM pour l'historique
        self.text_listbox = tk.Listbox(self.root, height=20, width=50)
        self.text_listbox.pack(side=tk.LEFT, padx=10, pady=10)

        self.image_listbox = tk.Listbox(self.root, height=20, width=50)
        self.image_listbox.pack(side=tk.RIGHT, padx=10, pady=10)

        # Associer un événement au clic sur une ligne de la liste de texte
        self.text_listbox.bind('<<ListboxSelect>>', self.handle_text_selection)

        # Associer un événement au clic sur une ligne de la liste d'image
        self.image_listbox.bind('<<ListboxSelect>>', self.handle_image_selection)

        # Ajouter un raccourci pour Ctrl + V
        self.root.bind('<Control-v>', self.paste_image)

        # Canvas pour afficher des images (miniatures)
        self.image_preview = tk.Label(self.root, width=100, height=100)  # Taille fixe
        self.image_preview.pack(pady=10)

        # Démarrer la vérification du presse-papier
        self.previous_clipboard = ""
        self.check_clipboard()

    def check_clipboard(self):
        # Vérifier le contenu du presse-papier
        try:
            current_clipboard = ImageGrab.grabclipboard()
        except Exception as e:
            current_clipboard = None

        if isinstance(current_clipboard, Image.Image):
            self.add_image_to_history(current_clipboard)
        else:
            current_clipboard = pyperclip.paste()
            if current_clipboard != self.previous_clipboard and current_clipboard != "":
                self.previous_clipboard = current_clipboard
                self.add_text_to_history(current_clipboard)

        self.root.after(100, self.check_clipboard)

    def add_text_to_history(self, text):
        if text not in self.text_history:
            self.text_history.append(text)
            self.text_listbox.insert(tk.END, f"Texte : {text[:30]}...")

    def image_to_hash(self, image):
        with io.BytesIO() as output:
            image.save(output, format="PNG")
            return hashlib.md5(output.getvalue()).hexdigest()

    def add_image_to_history(self, image):
        current_image_hash = self.image_to_hash(image)
        if current_image_hash in self.image_hashes:
            print("Image déjà présente dans l'historique.")
            return  # Sortir si l'image est déjà présente

        # Ajouter le hachage de l'image à l'ensemble
        self.image_hashes.add(current_image_hash)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        image.save(temp_file.name, format="PNG")
        self.image_history.append(temp_file.name)
        self.image_listbox.insert(tk.END, f"[Image]")

        self.display_image(image)  # Afficher l'image en taille fixe

    def display_image(self, image):
        # Redimensionner l'image pour la prévisualisation
        thumbnail = image.copy()
        thumbnail.thumbnail((150, 150))  # Taille fixe pour la prévisualisation
        self.thumbnail = ImageTk.PhotoImage(thumbnail)
        self.image_preview.config(image=self.thumbnail)

    def handle_text_selection(self, event):
        selected_index = self.text_listbox.curselection()
        if selected_index:
            selected_item = self.text_history[selected_index[0]]
            pyperclip.copy(selected_item)
            print(f"Texte copié : {selected_item}")

    def handle_image_selection(self, event):
        selected_index = self.image_listbox.curselection()
        if selected_index:
            selected_item = self.image_history[selected_index[0]]
            self.load_and_display_image(selected_item)
            self.paste_image(event)

    def load_and_display_image(self, file_path):
        image = Image.open(file_path)
        self.display_image(image)

    def paste_image(self, event):
        selected_index = self.image_listbox.curselection()
        if selected_index:
            selected_item = self.image_history[selected_index[0]]
            print("Tentative de copie de l'image dans le presse-papier.")
            success = self.copy_image_to_clipboard(selected_item)
            if success:
                print("Image copiée avec succès.")
            else:
                print("Échec de la copie de l'image.")

    def copy_image_to_clipboard(self, file_path):
        try:
            print(f"Chargement de l'image : {file_path}")

            image = Image.open(file_path)

            output = io.BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()

            return True
        
        except Exception as e:
            print(f"Erreur lors de la copie de l'image dans le presse-papier : {e}")
            return False

# Configurer et lancer l'application
if __name__ == "__main__":
    root = tk.Tk()
    app = ClipboardHistoryApp(root)
    root.mainloop()
