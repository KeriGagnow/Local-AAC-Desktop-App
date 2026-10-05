import importlib.util
import os
import subprocess
import sys
import threading
import uuid

# Prevent Windows proxy/firewall loopback interference
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

def ensure_dependencies():
    dependencies = {
        "customtkinter": "customtkinter",
        "chromadb": "chromadb",
        "ollama": "ollama",
        "pyttsx3": "pyttsx3",
    }

    for module_name, package_name in dependencies.items():
        if importlib.util.find_spec(module_name) is None:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

ensure_dependencies()

import customtkinter as ctk
import chromadb
import ollama
import pyttsx3

# ---------------------------
# 1. Local Database Setup with ChromaDB
# ---------------------------
chroma_client = chromadb.PersistentClient(path="./local_aac_db")
phrase_collection = chroma_client.get_or_create_collection(name="user_phrases")

if phrase_collection.count() == 0:
    seed_phrases = [
        "I would like a glass of water, please.",
        "I am feeling tired and need a break.",
        "Hello! It is great to see you today!",
        "Can you help me with this task?",
        "I am not feeling well and need assistance.",
        "Thank you for your help!",
        "I am excited to learn something new today.",
        "Could we go outside for a walk and get some fresh air?",
        "I am feeling frustrated and need some time to calm down.",
        "I need a quiet space right now."
    ]

    phrase_collection.add(
        documents=seed_phrases,
        ids=[f"phrase_{i}" for i in range(len(seed_phrases))]
    )


# ---------------------------
# 2. Desktop Interface with Asynchronous Ollama + TTS + Dynamic DB
# ---------------------------
class AACDesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AAC Assistant - with Ollama + Local RAG")
        self.geometry("740x640")
        self.minsize(580, 520)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.model_name = "phi3"
        self.ollama_client = ollama.Client(host="http://127.0.0.1:11434")

        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header Frame
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="AAC Assistant",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.pack(side="left")

        # Status badge (pinned to the far right)
        self.status_badge = ctk.CTkLabel(
            self.header_frame,
            text="Warming up model...",
            font=ctk.CTkFont(size=12),
            text_color="#FFA500"
        )
        self.status_badge.pack(side="right")

        # Dedicated Add Phrase button in the header
        self.add_phrase_btn = ctk.CTkButton(
            self.header_frame,
            text="+ Add Phrase",
            width=110,
            height=32,
            fg_color="#1F6FEB",
            hover_color="#388BFD",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.open_add_phrase_dialog
        )
        self.add_phrase_btn.pack(side="right", padx=(0, 15))

        # Shorthand Input Controls
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=20, pady=(5, 15), sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.shorthand_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Enter shorthand phrase (e.g., 'water', 'tired', 'hello')...",
            font=ctk.CTkFont(size=14),
            height=42
        )
        self.shorthand_entry.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        self.shorthand_entry.bind("<Return>", lambda _: self.start_generation())

        self.expand_btn = ctk.CTkButton(
            self.input_frame,
            text="Expand (LLM)",
            width=120,
            height=42,
            command=self.start_generation
        )
        self.expand_btn.grid(row=0, column=1, padx=(5, 10), pady=10)

        # Database retrieval display
        self.results_frame = ctk.CTkScrollableFrame(self, label_text="Database Matches (Click to Quick Select & Speak)")
        self.results_frame.grid(row=2, column=0, padx=20, pady=5, sticky="nsew")

        # Output / Speech Output Frame
        self.output_frame = ctk.CTkFrame(self)
        self.output_frame.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="ew")
        self.output_frame.grid_columnconfigure(0, weight=1)

        self.output_label = ctk.CTkLabel(
            self.output_frame,
            text="Ready to Speak Output:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.output_label.grid(row=0, column=0, padx=15, pady=(10, 2), sticky="w")

        # Action Buttons Container (Speak and Save)
        self.action_btn_frame = ctk.CTkFrame(self.output_frame, fg_color="transparent")
        self.action_btn_frame.grid(row=0, column=1, padx=15, pady=(10, 2), sticky="e")

        self.save_output_btn = ctk.CTkButton(
            self.action_btn_frame,
            text="💾 Save",
            width=80,
            height=32,
            fg_color="#30363D",
            hover_color="#484F58",
            font=ctk.CTkFont(size=12),
            command=self.save_current_output_to_db
        )
        self.save_output_btn.pack(side="left", padx=(0, 8))

        self.speak_btn = ctk.CTkButton(
            self.action_btn_frame,
            text="🔊 Speak",
            width=90,
            height=32,
            fg_color="#238636",
            hover_color="#2EA043",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.speak_current_output
        )
        self.speak_btn.pack(side="left")

        self.generated_text_var = ctk.StringVar(value="[No message generated yet]")
        self.output_display = ctk.CTkLabel(
            self.output_frame,
            textvariable=self.generated_text_var,
            font=ctk.CTkFont(size=16),
            anchor="w",
            wraplength=660,
            justify="left",
            text_color="#58A6FF"
        )
        self.output_display.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Trigger background warmup
        self.after(500, self.start_warmup)

    # ---------------------------
    # Speech Synthesis (TTS Engine)
    # ---------------------------
    def speak_text(self, text: str):
        """Converts text string into offline speech using Windows SAPI5 in a background thread."""
        if not text or text.startswith("[No message") or text.startswith("Error"):
            return

        def _tts_worker():
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", 160)
                engine.setProperty("volume", 1.0)
                engine.say(text)
                engine.runAndWait()
                engine.stop()
            except Exception as e:
                print(f"[TTS Error] Speech playback failed: {e}")

        threading.Thread(target=_tts_worker, daemon=True).start()

    def speak_current_output(self):
        current_text = self.generated_text_var.get()
        self.speak_text(current_text)

    # ---------------------------
    # Dynamic Database Actions
    # ---------------------------
    def open_add_phrase_dialog(self):
        """Displays modal to register a new communication phrase."""
        dialog = ctk.CTkInputDialog(
            text="Enter full phrase to teach your database:",
            title="Add Communication Phrase"
        )
        user_input = dialog.get_input()

        if user_input and user_input.strip():
            clean_phrase = user_input.strip()
            new_id = f"custom_{uuid.uuid4().hex[:8]}"

            # Add to local ChromaDB
            phrase_collection.add(
                documents=[clean_phrase],
                ids=[new_id]
            )

            self.generated_text_var.set(f"Added to database: \"{clean_phrase}\"")
            self.speak_text("New phrase saved.")

            # Refresh matches if user has typed query
            query = self.shorthand_entry.get().strip()
            self.update_rag_recommendations(query if query else "common daily needs")

    def save_current_output_to_db(self):
        """Saves whatever sentence is currently displayed in the Ready to Speak output box."""
        current_text = self.generated_text_var.get().strip()
        if not current_text or current_text.startswith("[No message") or current_text.startswith("Error"):
            return

        new_id = f"saved_llm_{uuid.uuid4().hex[:8]}"
        phrase_collection.add(
            documents=[current_text],
            ids=[new_id]
        )
        self.speak_text("Phrase saved to library.")

    # ---------------------------
    # Model Lifecycle & Worker Logic
    # ---------------------------
    def start_warmup(self):
        threading.Thread(target=self.warmup_model, daemon=True).start()

    def warmup_model(self):
        try:
            self.ollama_client.generate(model=self.model_name, prompt="ready", keep_alive="24h")
            self.after(
                0,
                lambda: self.status_badge.configure(
                    text=f"Model ready ({self.model_name})",
                    text_color="#3FB950",
                ),
            )
        except Exception as e:
            print(f"[Ollama Error] Warmup failure: {e}")
            self.after(
                0,
                lambda: self.status_badge.configure(
                    text="Ollama offline",
                    text_color="#F85149",
                ),
            )

    def start_generation(self):
        query = self.shorthand_entry.get().strip()
        if not query:
            return

        self.expand_btn.configure(state="disabled", text="Generating...")
        self.update_rag_recommendations(query)

        threading.Thread(
            target=self.run_ollama_pipeline,
            args=(query,),
            daemon=True,
        ).start()

    def update_rag_recommendations(self, query: str):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        results = phrase_collection.query(query_texts=[query], n_results=4)
        docs = results.get("documents", [[]])[0]

        for phrase in docs:
            btn = ctk.CTkButton(
                self.results_frame,
                text=phrase,
                anchor="w",
                height=38,
                fg_color="#21262D",
                hover_color="#30363D",
                font=ctk.CTkFont(size=13),
                command=lambda p=phrase: self.select_and_speak(p)
            )
            btn.pack(fill="x", padx=10, pady=4)

    def select_and_speak(self, phrase: str):
        self.generated_text_var.set(phrase)
        self.speak_text(phrase)

    def run_ollama_pipeline(self, shorthand_input: str):
        try:
            rag_context = phrase_collection.query(
                query_texts=[shorthand_input],
                n_results=2,
            )
            reference_phrases = rag_context.get("documents", [[]])[0]
            context_string = "\n".join([f"- {p}" for p in reference_phrases])

            system_prompt = (
                "You are an assistive Augmentative and Alternative Communication (AAC) speech engine. "
                "Convert the user's shorthand input into a single, complete, natural, polite first-person statement. "
                "Output ONLY the final sentence. Do not include quotes, preamble, greetings, or explanations.\n\n"
                f"Reference user communication phrases:\n{context_string}"
            )

            response = self.ollama_client.generate(
                model=self.model_name,
                prompt=f"Shorthand: {shorthand_input}\nFull Statement:",
                system=system_prompt,
                keep_alive="24h",
                options={"temperature": 0.2, "top_p": 0.9}
            )
            clean_output = response.get("response", "").strip().strip('"')
            self.after(0, self.update_output_ui, clean_output)
        except Exception as e:
            print(f"[Ollama Error] Generation failed: {e}")
            self.after(0, self.update_output_ui, f"Error generating speech: {e}")

    def update_output_ui(self, result_text: str):
        self.generated_text_var.set(result_text)
        self.expand_btn.configure(state="normal", text="Expand (LLM)")
        self.speak_text(result_text)

    def on_close(self):
        try:
            self.ollama_client.generate(model=self.model_name, prompt="exit", keep_alive="0s")
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    app = AACDesktopApp()
    app.mainloop()