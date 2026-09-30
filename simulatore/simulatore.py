import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class DRSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulatore Demand Response")
        self.root.geometry("900x700")
        
        self.lmp_data = None
        
        self.create_widgets()

    def create_widgets(self):
        # Frame per i Controlli di Input
        control_frame = ttk.LabelFrame(self.root, text="Parametri di Configurazione")
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        # Pulsante Caricamento Dati
        self.btn_load = ttk.Button(control_frame, text="Carica CSV Dati LMP", command=self.load_data)
        self.btn_load.grid(row=0, column=0, padx=10, pady=10)
        
        self.lbl_data_status = ttk.Label(control_frame, text="Nessun file caricato", foreground="red")
        self.lbl_data_status.grid(row=0, column=1, padx=10, pady=10)

        # Parametro: Prezzo Bitcoin
        ttk.Label(control_frame, text="Prezzo BTC ($):").grid(row=1, column=0, sticky=tk.E, padx=5, pady=5)
        self.ent_btc_price = ttk.Entry(control_frame)
        self.ent_btc_price.insert(0, "25000") # Valore dell'articolo
        self.ent_btc_price.grid(row=1, column=1, padx=5, pady=5)

        # Parametro: MWh per Bitcoin
        ttk.Label(control_frame, text="Difficoltà (MWh/BTC):").grid(row=1, column=2, sticky=tk.E, padx=5, pady=5)
        self.ent_mwh_per_btc = ttk.Entry(control_frame)
        self.ent_mwh_per_btc.insert(0, "143") # Valore dell'articolo
        self.ent_mwh_per_btc.grid(row=1, column=3, padx=5, pady=5)

        # Parametro: Costo Elettricità
        ttk.Label(control_frame, text="Costo Elettricità ($/MWh):").grid(row=2, column=0, sticky=tk.E, padx=5, pady=5)
        self.ent_elec_cost = ttk.Entry(control_frame)
        self.ent_elec_cost.insert(0, "30")
        self.ent_elec_cost.grid(row=2, column=1, padx=5, pady=5)

        # Pulsante Avvio Simulazione
        self.btn_run = ttk.Button(control_frame, text="Avvia Simulazione", command=self.run_simulation, state=tk.DISABLED)
        self.btn_run.grid(row=2, column=3, padx=10, pady=10)

        # Frame per il Grafico (Matplotlib)
        self.plot_frame = ttk.Frame(self.root)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def load_data(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if filepath:
            try:
                df = pd.read_csv(filepath)
                if 'LMP' not in df.columns:
                    messagebox.showerror("Errore", "Il file CSV deve contenere una colonna chiamata 'LMP'")
                    return
                self.lmp_data = df['LMP'].values
                self.lbl_data_status.config(text=f"Dati caricati: {len(self.lmp_data)} ore", foreground="green")
                self.btn_run.config(state=tk.NORMAL)
            except Exception as e:
                messagebox.showerror("Errore di caricamento", str(e))

    def run_simulation(self):
        try:
            btc_price = float(self.ent_btc_price.get())
            mwh_per_btc = float(self.ent_mwh_per_btc.get())
            elec_cost = float(self.ent_elec_cost.get())
        except ValueError:
            messagebox.showerror("Errore", "Inserisci valori numerici validi nei parametri.")
            return

        # 1. Calcolo Ricavo Netto di Mining r(t)
        # Ricavo = (Prezzo BTC / Energia per minarlo) - Costo Elettricità
        p_b = btc_price / mwh_per_btc
        r_t = p_b - elec_cost

        # Calcoliamo il ricavo di partecipazione di base per 1 MW
        mean_lmp = np.mean(self.lmp_data)
        annual_dr_reward = mean_lmp * len(self.lmp_data)

        thresholds = np.arange(35, 71, 1) # Range LMP da 35 a 70 $/MWh come in Figura 8
        profits = []

        # 2. Implementazione Eq. (1a) dell'articolo
        for threshold in thresholds:
            # Tasso di dispacciamento d(t): 1 se LMP > soglia (il miner viene interrotto)
            deployment = (self.lmp_data > threshold).astype(int)
            
            # Perdita: r(t) moltiplicato per le ore in cui si è stati interrotti
            loss_mining = np.sum(deployment * r_t)
            
            # Profitto totale: Ricavo DR - Perdita derivante dall'interruzione del mining
            profit = annual_dr_reward - loss_mining
            profits.append(profit)

        self.plot_results(thresholds, profits)

    def plot_results(self, thresholds, profits):
        self.ax.clear()
        
        # Traccia la curva del Price-driven DR 
        self.ax.plot(thresholds, profits, label='Price-driven DR', color='magenta', linewidth=2)
        
        self.ax.axhline(y=98000, color='orange', linestyle='-', label='Responsive Reserve Service')
        self.ax.axhline(y=50000, color='teal', linestyle='-', label='Emergency Response Service')

        self.ax.set_title("Annual per unit profit for 1 MW Demand Response Capacity", fontsize=12)
        self.ax.set_xlabel("LMP threshold of deploying DR ($/MWh)", fontsize=10)
        self.ax.set_ylabel("Annual per unit profit ($/MW)", fontsize=10)
        self.ax.set_xlim(35, 70)
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.ax.legend(loc='lower right')
        
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = DRSimulatorApp(root)
    root.mainloop()