# 📻 Webrádió (ESP32-S3-Zero + CircuitPython)

Ez a projekt egy egyszerű, otthon is könnyen megépíthető internetes rádiót valósít meg.
A célja, hogy kevés és olcsó alkatrészek segítségével online rádióadókat hallgathassunk.

A kód **CircuitPython** nyelven íródott, így a módosítása és használata kezdők számára is egyszerű.

## 🛠️ Hogyan épül fel?

A rendszer szíve egy ESP32 kártya, amely az internetről letölti a zenei adatfolyamot, és egy digitális-analóg átalakítón keresztül hanggá alakítja.

![Működési infografika](images/1v02_infografika.png)

### Szükséges eszközök:
*   **Vezérlő:** ESP32-Zero / S3
*   **Hangkártya (DAC):** MAX98357a
*   **Potméter:** 56 Ohm / 1W
*   **Hangszóró:** 8 Ohm / 1W
*   **Szoftver:** CircuitPython 10.x

## 🚀 Telepítés 3 lépésben

1.  **CircuitPython telepítése:**
    Csatlakoztasd az ESP32-t a számítógéphez, és telepítsd rá a megfelelő [CircuitPython](https://circuitpython.org/) rendszert.
    Ekkor megjelenik egy `CIRCUITPY` nevű meghajtó a számítógépeden (mint egy pendrive).

3.  **Fájlok másolása:**
    Töltsd le ezt a repót (vagy a ZIP-et), és másold át a tartalmát a `CIRCUITPY` meghajtó gyökerébe.

4.  **Beállítás (Wi-Fi):**
    A `settings.toml` fájlban add meg a saját Wi-Fi adataidat
    A kedvenc rádióállomásaid linkjét aktiváld a főprogramban - cope.py

## ⚙️ Használat

A bekapcsolás után az eszköz automatikusan csatlakozik a megadott Wi-Fi hálózatra és elindítja a lejátszást.
Ha módosítani szeretnéd a kódot, csak szerkeszd a `code.py` fájlt bármilyen szövegszerkesztővel.
