# wp-to-html
whatsapp çıkan sohbeti html yapmanın yolu.
Bu html, düz yazı ve resimlerin olduğu yedek klasörünü, oldukça düzgün web sayfası gibi göstermeye yara. Sanki whatsapp mesajlarına bakarmış gibi.

Grup gizliliği varsa önce gizliliği kapatın, yoksa içerik inmez.
sonra:
⋮ → More → Export chat  ... Include media  --> ZIP formatında iner

Zip formatını bir klasöre çıkarın. pyw çalıştırın, web sayfası olarak oluşsun, bu web sayfasına gir mesajları seç, yeni yeni web sayfası seçilen kısmı oluşur (word belgesi olarak seçilenlerin çıkarılması geliştirilme aşamasında)

whatsapp_to_html.py Zip ile indirilmiş Whatsapp grup / kişi dosyasını bir klasöre açın. Bunu çalıştırınca o klasörü gösterin. Klasörün yanına html oluşur, whatsapp tarzı resimler ve mesajlar düzgün şekilde gözükür
