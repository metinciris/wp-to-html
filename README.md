# wp-to-html (WhatsApp to HTML) `v1.1`

Whatsapp indirilen arşivi web sayfasına dönüştürür. İçinden vaka seçtirip ayrı web sayfası olarak kaydetmeye yarar.

WhatsApp üzerinden yürütülen tıbbi vaka tartışmalarını, eğitim ve sunum amacıyla profesyonel, anonim ve taranabilir bir HTML arşivine dönüştüren masaüstü uygulamasıdır. Özellikle mikroskobik görüntüler ve radyolojik tetkiklerin yoğun paylaşıldığı gruplar için optimize edilmiştir.



## ✨ Öne Çıkan Özellikler

* **🔍 Akıllı Mikroskop Zoom:** Fare tekerleği (mouse wheel) ile görüntülere yüksek çözünürlüklü yakınlaştırma.
* **👤 Gelişmiş Anonimlik:** Tek tıkla tüm isimleri gizleme/gösterme özelliği (KVKK uyumlu paylaşım için).
* **📂 Seçici Paketleme (Vaka Modu):** Yüzlerce mesaj arasından sadece ilgili vakayı seçip, resimleriyle birlikte ayrı bir klasöre "mini-arşiv" olarak çıkarma.
* **📦 Tam Yedekleme:** Tüm sohbeti tek tıkla medya dosyalarıyla birlikte HTML formatında paketleme.
* **🏷️ Altyazı Entegrasyonu:** Resimlerin hemen altına yazılan "CD56", "PanCK", "Kromo" gibi notları otomatik olarak galeri moduna (caption) taşıma.
* **🎨 Modern Arayüz:** Göz yormayan antrasit/safir teması ve okunaklı tipografi.

## 🚀 Kurulum ve Kullanım

### 1. Hazırlık
WhatsApp üzerinde ilgili sohbetin ayarlarına girin:
* **Diğer > Sohbeti Aktar > Medyayı Dahil Et** seçeneğine tıklayın.
* Gelen `.zip` dosyasını bir klasöre çıkartın.

### 2. Uygulamayı Çalıştırma
Uygulama Python tabanlıdır. `whatsapp_to_html.py` (veya .pyw) dosyasını çalıştırın:
```bash
python whatsapp_to_html.py
```

### 3. Arşivleme Adımları
1.  **Klasör Seç:** WhatsApp'tan çıkarttığınız klasörü seçin.
2.  **İncele:** Tarayıcıda açılan panelde vaka tartışmalarını inceleyin.
3.  **Paketle:** * Sadece belirli mesajları istiyorsanız "Seçim Modu"nu açıp mesajları seçin ve **"Vakayı Paketle"** deyin.
    * Tüm grubu arşivlemek için **"Herşeyi Paketle"** deyin.



## 🛠 Teknik Detaylar
* **Dil:** Python 3.x
* **Arayüz:** Tkinter (GUI) + HTML5/CSS3/JS (Web Dashboard)
* **Sunucu:** Local Python HTTP Server (Verileriniz dışarı çıkmaz, tamamen yerel çalışır).

## 📝 Versiyon Geçmişi
* **v1.1:** Dinamik buton metinleri, tam anonimlik modu ve geliştirilmiş vaka seçim alanı eklendi.
* **v1.0:** İlk kararlı sürüm; Zoom, Kaydırma ve Temel Paketleme özellikleri.

## 🤝 Katkıda Bulunma
Bu proje tıbbi eğitim ve vaka paylaşımını kolaylaştırmak için geliştirilmiştir. Pull request göndererek veya "Issue" açarak katkıda bulunabilirsiniz.

---
**Geliştirici:** [Metin Çiriş](https://github.com/metinciris)  
**Lisans:** MIT

---
