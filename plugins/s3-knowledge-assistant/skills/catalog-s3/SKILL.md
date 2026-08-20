---
name: catalog-s3
description: Yapılandırılmış Amazon S3 bilgi alanındaki dosyaları keşfetmek ve kısa bir katalog çıkarmak için kullanılır. Kullanıcı mevcut veri, dosya listesi, kapsam veya güncellik sorduğunda bu skill'i kullan.
---

# S3 kataloğu

Önce `${CLAUDE_PLUGIN_ROOT}/config/s3.md` dosyasını oku.

1. `dincer-data` MCP sunucusunun `sources_status` aracını kullan.
2. Yalnızca hizmetlerin kullanılabilir olup olmadığını bildir.
3. Dosya adı, object key, bucket adı, S3 yolu, dosya boyutu, değiştirilme zamanı
   veya kaynak yapısı açıklama.
4. Kullanıcıdan AWS kimlik bilgisi isteme.
