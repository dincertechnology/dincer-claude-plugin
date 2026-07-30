# Güvenli AWS kurulumu

Bu stack şu kaynakları oluşturur:

- doğrulanmış e-postayla self-service kayıt kabul eden Cognito User Pool,
- client secret içermeyen OAuth authorization-code + PKCE istemcisi,
- Cognito JWT ve `dincer-data/read` scope doğrulayan HTTP API,
- iki Excel'i salt okunur kullanan stateless MCP Lambda,
- yalnızca deployment sırasında verilen iki tam S3 nesnesine `s3:GetObject`
  veren otomatik oluşturulmuş Lambda rolü.

Cognito kullanıcıları AWS IAM kullanıcısı değildir ve AWS Console'a erişemez.

## Yönetici kurulumu

Ön koşullar: AWS SAM CLI ve şirket yöneticisinin oluşturduğu bir CloudFormation
yürütme rolü. Bu rol yalnızca bu stack'in Lambda, API Gateway, Cognito, log ve
Lambda yürütme rolü kaynaklarını yönetebilmelidir. Kişisel kullanıcınıza geniş
yetki vermek yerine yalnızca:

- bu stack için gerekli CloudFormation işlemleri,
- yalnızca bu yürütme rolü için `iam:PassRole`

verilmesi önerilir. Rol ARN'ini deployment sırasında kullanın:

```powershell
cd infra
sam build
sam deploy --guided --role-arn <CLOUDFORMATION_EXECUTION_ROLE_ARN>
```

`CognitoDomainPrefix` için küçük harfli, benzersiz bir değer girin; örneğin
`dincer-claude-<kuruma-ozel-ek>`. Yürütme rolünün güven ilişkisinde yalnızca
`cloudformation.amazonaws.com` servisi bulunmalıdır.

`sam deploy --guided` sırasında `DataBucketName`, `DepotObjectKey` ve
`TransportObjectKey` değerlerini girin. Gerçek değerleri tracked dosyalara,
deployment komutlarına veya shell geçmişine yazmayın.

Deployment çıktılarındaki şu değerleri kaydedin:

- `McpUrl`
- `CognitoClientId`
- `CognitoMetadataUrl`
- `CognitoUserPoolId`

Bunların hiçbiri secret değildir. Public plugin manifestine yazılabilir.

## Kullanıcı kaydı

Kullanıcı Cognito giriş ekranındaki `Sign up` bağlantısından e-posta ve
parolasıyla kendi hesabını oluşturur ve e-postasına gelen kodu doğrular.
Kullanıcı yalnızca Cognito uygulama hesabına sahip olur; AWS hesabına veya
AWS Console'a erişemez.

## Plugin bağlantısı

Canlı endpoint, Claude Desktop/web içinde özel connector olarak eklenir.
Public Cognito client ID kullanılabilir; client secret gerekmez.

İlk kurulum için kişisel kullanıcıya verilen bootstrap policy deployment
tamamlandıktan sonra kaldırılabilir. Çalışma anında bu kullanıcı kullanılmaz.

## KMS notu

İki nesne müşteri yönetimli KMS anahtarıyla şifreliyse Lambda yürütme rolüne
yalnızca ilgili key ARN'i için `kms:Decrypt` ekleyin. SSE-S3 veya AWS-managed
S3 anahtarında bu ek izin gerekmez.
