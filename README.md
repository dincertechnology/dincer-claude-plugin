# Dincer Logistics Claude Connector

![Dincer Logistics connector icon](assets/dincer-connector-icon.png)

Claude için Dincer Logistics'in yetkili iki Excel veri kaynağından salt okunur
ve kaynaklı yanıt üreten herkese açık marketplace eklentisi.

## Şu anki yapı

```text
.claude-plugin/marketplace.json
plugins/s3-knowledge-assistant/
├── .claude-plugin/plugin.json
├── .mcp.json
├── commands/
│   └── s3-ask.md
├── config/
│   ├── lambda-s3-read-policy.json
│   └── s3.md
└── skills/
    ├── answer-from-s3/SKILL.md
    └── catalog-s3/SKILL.md
infra/
├── template.yaml
└── backend/
    ├── app.py
    ├── excel_reader.py
    └── requirements.txt
```

## Veri kaynakları

Connector yalnızca onaylı depo bilgileri ve taşıma fiyat listesi çalışma
kitaplarını okur.

Kaynak ayarları `plugins/s3-knowledge-assistant/config/s3.md`, en az yetkili
Lambda politikası ise yanındaki `lambda-s3-read-policy.json` dosyasındadır.

## Güvenli AWS bağlantısı

1. Kullanıcılar Cognito'da kendi e-postalarını doğrulayarak kayıt olur; AWS IAM
   kullanıcısı olmazlar.
2. API Gateway yalnızca geçerli Cognito access token ve `dincer-data/read`
   scope bulunan MCP çağrılarını Lambda'ya geçirir.
3. Lambda, deployment sırasında otomatik üretilen servis rolüyle çalışır.
4. Rol yalnızca deployment parametreleriyle verilen iki S3 nesnesinde
   `s3:GetObject` yetkisine sahiptir.
5. Standart Lambda loglama izinleri deployment sırasında otomatik eklenir.

Access key, secret key ve parola oluşturulmaz. Lambda SDK'sı rolün geçici STS
kimlik bilgilerini otomatik kullanır. Bucket müşteri yönetimli KMS anahtarı
kullanıyorsa yalnızca o anahtar ARN'i için ayrıca `kms:Decrypt` eklenmelidir.

AWS yöneticisi kurulumu için [infra/README.md](infra/README.md) dosyasını izler.
Kullanıcı parolası, token veya AWS credential'ı repoda tutulmaz.

## Claude Desktop/web bağlantısı

Plugin skill'leri ve güvenli MCP bağlantısını birlikte kurar. Plugin
kurulduktan sonra `Dincer Logistics` connector kartındaki `Connect` ile Cognito
kayıt/giriş akışı başlatılır. OAuth Client ID, DCR endpoint'i tarafından
yalnızca Claude'un resmi callback adresi için otomatik sağlanır; kullanıcı URL,
Client ID veya Client Secret girmez.

## Anthropic Directory review access

No pre-created test credentials are provided. Reviewers can use the production
self-registration flow:

1. Connect to the `Dincer Logistics` connector.
2. Select **Sign up** on the Amazon Cognito sign-in page.
3. Register with an email address controlled by the reviewer.
4. Enter the verification code sent to that address.
5. Sign in and test the read-only data-source listing and search tools.

Self-registered users receive only the `dincer-data/read` OAuth scope. They do
not receive an AWS IAM user, AWS credentials, write access, or access to the S3
console.

## Yerel deneme

Claude Code içinde:

```text
/plugin marketplace add C:\Dincer Claude Plugin
/plugin install s3-knowledge-assistant@dincer-claude-plugins
/reload-plugins
```

Örnek kullanım:

```text
/s3-knowledge-assistant:s3-ask Son çeyreğin satış özetini çıkar
/s3-knowledge-assistant:catalog-s3
```

Marketplace doğrulaması:

```powershell
claude plugin validate "C:\Dincer Claude Plugin"
```

## GitHub üzerinden kurulum

Kullanıcılar:

```text
/plugin marketplace add dincertechnology/dincer-claude-plugin
/plugin install s3-knowledge-assistant@dincer-claude-plugins
```

komutlarıyla kurabilir.

## Örnekler

- "Depo kaynaklarında İstanbul için hangi kayıtlar var?"
- "Taşıma fiyat listesinde Ankara çıkışlı eşleşmeleri bul."
- "Yetkili veri kaynaklarının son güncellenme tarihlerini göster."

## Gizlilik ve destek

- [Dincer Logistics Gizlilik ve Çerez Politikası](https://dincerlogistics.com/gizlilik-ve-cerez-politikasi/)
- [Connector veri işleme bildirimi](https://github.com/dincertechnology/dincer-claude-plugin/blob/main/docs/privacy-policy.md)
- Web sitesi: [dincerlogistics.com](https://dincerlogistics.com/)
- Destek: [info@dincerlojistik.com](mailto:info@dincerlojistik.com)
