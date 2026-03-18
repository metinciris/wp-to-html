# 📁 Anonim WhatsApp Vaka Arşivi (wp-to-html) `v1.0`

WhatsApp üzerinden paylaşılan tıbbi vaka tartışmalarını, eğitim ve sunum amacıyla profesyonel, **anonim** ve taranabilir bir HTML arşivine dönüştüren masaüstü uygulamasıdır. Özellikle patoloji, radyoloji gibi mikroskobik veya radyolojik görüntülerin yoğun paylaşıldığı uzmanlık alanları için optimize edilmiştir.



## ✨ Öne Çıkan Özellikler

* **👤 Gelişmiş Anonimlik:** Tek tıkla gönderici isimlerini gizleme/gösterme. İsimler gizliyken yapılan paketlemeler tamamen anonim (KVKK uyumlu) olarak kaydedilir.
* **🔍 Akıllı Mikroskop Zoom:** Fare tekerleği (mouse wheel) ile görüntülere yüksek çözünürlüklü yakınlaştırma (%2000'e kadar).
* **📂 Seçici Paketleme (Vaka Modu):** Yüzlerce mesaj arasından sadece ilgili vakayı seçip, resimleriyle birlikte ayrı bir "vaka klasörü" olarak çıkarma.
* **📦 Tam Yedekleme:** Tüm sohbeti tek tıkla medya dosyalarıyla birlikte tek bir HTML sayfasında toplama.
* **🏷️ Altyazı Entegrasyonu:** Resim altına yazılan "CD56", "PanCK", "Kromo" gibi notları otomatik algılar ve galeri modunda altyazı olarak gösterir.
* **🎨 Modern & Pastel Arayüz:** Göz yormayan antrasit/safir teması, yüksek kontrast ve okunaklı tıbbi dokümantasyon stili.

---

## 📂 Klasör Yapısı

Projeyi bilgisayarınıza indirdiğinizde aşağıdaki yapıyla karşılaşacaksınız:

* **`src/`**: Uygulamanın Python kaynak kodu (`whatsapp_to_html.py`).
* **`bin/`**: Python kurulu olmayan sistemler için hazır çalıştırılabilir uygulama (`.exe`).
* **`assets/`**: Uygulama içi görseller ve ikonlar.

---

## 🚀 Kurulum ve Kullanım

### 1. Hazırlık
WhatsApp üzerinde ilgili sohbetin ayarlarına girin:
* **Diğer > Sohbeti Aktar > Medyayı Dahil Et** seçeneğine tıklayın.
* Gelen `.zip` dosyasını bir klasöre çıkartın.

### 2. Uygulamayı Çalıştırma
* **Hızlı Kullanım:** `bin/Anonim_Whatsapp_Vaka_Arsivi.exe` dosyasını çalıştırın.
* **Python ile Çalıştırma:**
    ```bash
    python src/whatsapp_to_html.py
    ```

### 3. Arşivleme Adımları
1.  **Klasör Seç:** WhatsApp'tan çıkarttığınız (içinde mesajlar ve resimler olan) klasörü seçin.
2.  **İncele:** Tarayıcıda açılan panelde vakaları inceleyin. Arama kutusunu kullanarak tanı veya boya ismine göre filtreleme yapabilirsiniz.
3.  **Paketle:**
    * **Vakayı Paketle:** Seçim modunu açıp mesajları işaretleyin ve butona basın. Seçtiğiniz isimle ana dizinde yeni bir klasör oluşur.
    * **Herşeyi Paketle:** Tüm sohbeti olduğu gibi yedeklemek için kullanın.



---

## 🛠 Teknik Detaylar
* **Dil:** Python 3.x
* **Arayüz:** Tkinter (GUI) + HTML5/CSS3/JS (Dashboard)
* **Güvenlik:** Local Python HTTP Server kullanılır. Verileriniz internete çıkmaz, tamamen kendi bilgisayarınızda işlenir.

## 📝 Versiyon Geçmişi
* **v1.0:** İlk Kararlı Sürüm. Dinamik isim gizleme, vaka seçimi, gelişmiş zoom ve pastel tema iyileştirmeleri.

## 🤝 Katkıda Bulunma
Bu proje tıbbi eğitim ve vaka paylaşımını kolaylaştırmak için geliştirilmiştir. Katkıda bulunmak isterseniz lütfen bir "Issue" açın veya Pull Request gönderin.

---
**Geliştirici:** [Metin Çiriş](https://github.com/metinciris)  
**Lisans:** MIT

---
