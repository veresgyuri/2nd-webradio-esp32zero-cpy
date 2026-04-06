# 📻 ESP32-S3-Zero webrádió - CircuitPython

Sorry folks, this repo comes with Hungarian comments only 🙂<br><br>
Ez a projekt egy egyszerű, otthon is könnyen megépíthető internetes rádiót valósít meg.  
A célja, hogy kevés és olcsó (~5eFt) alkatrészek segítségével online rádióadókat hallgathassunk.

A kód **CircuitPython** nyelven íródott, így a módosítása és használata kezdők számára is egyszerű.


## 🛠️ Szükséges eszközök

*   **Vezérlő:** [ESP32-S3-Zero](https://www.waveshare.com/wiki/ESP32-S3-Zero?srsltid=AfmBOorfqn8I1ezSHGBBIlw2pK0BOvZDR--FL35lBhwTRSxVBlx0neT8)
*   **Hangkártya (DAC):** [MAX98357a](https://www.hestore.hu/prod_10045704.html?gad_source=1&gad_campaignid=21163162680&gclid=Cj0KCQiAwYrNBhDcARIsAGo3u31R_6zZiZZxwd9yj28r72FO6T526xeCuA3uZ3R8JjvgYFxM5n-z6VUaAoVbEALw_wcB)
*   **Rotary enkóder:** [EC-11](https://modulshop.hu/ec-11-rotary-encoder-modul?gad_source=1&gad_campaignid=21423119443&gclid=Cj0KCQiAwYrNBhDcARIsAGo3u31sm7AfpCMMxEo-_kZ6QTVhSEUY2_c3FlV4BZJfM9iKV7LHxtDuHLsaAphYEALw_wcB)
*   **Potméter:** 56 Ohm / 1W
*   **Hangszóró:** 8 Ohm / 1W
*   **Szoftver:** CircuitPython 10.x.x

## ⚙️ Működés

A rendszer szíve egy ESP32 kártya, amely az internetről letölti a zenei adatfolyamot, és egy digitális-analóg átalakítót vezérelve hanggá alakítja.  
  
**Fejlesztési életciklus**

**0v0** - Csak egy állomást játszik --> állomás váltás a code.py kódban - a link átírásával  

![Működési infografika 0v0](images/0v0_infografika.jpg)

**1v22** - Állomáslista külön fájlban + egy 'tekerős nyomógomb' ami a váltást és az első állomásra ugrást kezeli  

![Működési infografika 1v22](images/1v22_infografika.jpg)

**2v13** - OLED kijelző implementálása és ver2 kód véglegesítése  

![Működési infografika 2v13](images/2v12_infografika.jpg)  

**3v00** - Procedurális eljárású kód átírása OOP-re  
3v.. - Állomáslista lapozó menü létrehozása  

![Állomás megjelenítés lejátszáskor](images/OLED_station_name.jpg)  

Rövid gombnyomásra  
![Menübe lépés](images/OLED_menu.jpg)  

Enkóder tekerés LISTA módban  
![Állomások lapozása](images/OLED_list.jpg)  
![Állomások lapozása](images/OLED_lista.jpg)  
**Rövid gombnyomás** - a kiválasztott állomásra ugrik  
**Hosszú gombnyomás** - továbbra is RESET funkció  

## 🚀 Telepítés 3 lépésben

1.  **CircuitPython firmware telepítése:**
    Csatlakoztasd az ESP32-t a számítógéphez, és telepítsd rá a lapkának megfelelő [CircuitPython](https://circuitpython.org/downloads) rendszert.
    Ekkor megjelenik egy `CIRCUITPY` nevű meghajtó a számítógépeden (mint egy pendrive).

3.  **Fájlok másolása:**
    Ha akarod, töltsd le ezt a repót (vagy a ZIP-et), és másold át a `CIRCUITPY` meghajtó gyökerébe.
    De a működéshez csak erre a három fájlra lesz szükséged - a gyökérbe<br>
    ![Szükséges filék](images/need_this_3_files.png)  

    Valamint ezeket kell felmásolnod a /lib mappába<br>
    ![Szükséges modulok](images/need_to_lib_folder.png)   

5.  **Beállítás (Wi-Fi & Állomáslista):**
    A kedvenc rádióállomásaid adatait írd be a `stations.json` fájlba.
    A `settings.toml` fájlban add meg a Wi-Fi elérés adataidat.<br>
    Ez legyen a formátum:  
    CIRCUITPY_WIFI_SSID = "your ssid name"  
    CIRCUITPY_WIFI_PASSWORD = "your pwd"

## ⚙️ Használat

A bekapcsolás után az eszköz automatikusan csatlakozik a megadott Wi-Fi hálózatra és elindítja a lejátszást.  
A kijelzőn kicsi betükkel látod, ha még nincs Wifi kapcsolat.  
Sikeres lejátszáskor a kijelző nagy karaterre vált - kiírva a streamelt állomás nevét.  
Az állomásokat az enkóder tekerésével tudod váltani.  
A tekerőgombot megnyomva újraindul az eszkőz és a lista első állomására ugrik.

## 🖼️ Fotók

Javaslom, hogy nézz be az 📁/images mappába is.
