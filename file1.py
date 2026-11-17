import tkinter as tk

# Ana pencereyi oluşturuyoruz
pencere = tk.Tk()
pencere.title("Selam Uygulaması")
pencere.geometry("300x200")  # Pencere boyutu (genişlik x yükseklik)

# Pencerenin ortasına "Selam" yazan bir etiket (label) ekliyoruz
etiket = tk.Label(pencere, text="Selam", font=("Arial", 24))
etiket.pack(expand=True)

# Uygulamanın açık kalmasını sağlayan döngü
pencere.mainloop()
