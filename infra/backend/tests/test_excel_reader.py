import io
import unittest

from openpyxl import Workbook

from excel_reader import search_workbook


class ExcelReaderTest(unittest.TestCase):
    def test_finds_turkish_text_and_limits_output(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Fiyatlar"
        sheet.append(["Çıkış", "Varış", "Fiyat"])
        sheet.append(["NoktaA", "NoktaB", 1250])
        sheet.append(["NoktaC", "NoktaD", 900])
        buffer = io.BytesIO()
        workbook.save(buffer)

        matches, truncated = search_workbook(
            buffer.getvalue(), "noktaa noktab", "tasima", 1
        )

        self.assertFalse(truncated)
        self.assertEqual(1, len(matches))
        self.assertEqual("1250", matches[0]["values"]["Fiyat"])

    def test_ftl_province_uses_named_center_and_returns_both_origins(self):
        workbook = Workbook()
        for index, (title, price) in enumerate(
            (("A Çıkış", 12345.4), ("B Çıkış", 23456.6))
        ):
            sheet = workbook.active if index == 0 else workbook.create_sheet()
            sheet.title = title
            sheet.append([])
            sheet.append([None, "81 İl Fiyat Teklifi"])
            sheet.append([None, "İl", "İlçe", "Kamyon", "Kırkayak", "Tır"])
            sheet.append([None, "Testil", "Testil", price, 30000, 40000])
            sheet.append([None, "Testil", "Testçe", 50000, 60000, 70000])
        buffer = io.BytesIO()
        workbook.save(buffer)

        matches, truncated = search_workbook(
            buffer.getvalue(), "Testil için fiyat nedir?", "tasima", 8
        )

        self.assertFalse(truncated)
        self.assertEqual(["12345 TL", "23457 TL"], [m["values"]["Kamyon"] for m in matches])
        self.assertTrue(all(m["values"]["İlçe"] == "Testil" for m in matches))

    def test_ftl_district_overrides_province_center(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "A Çıkış"
        sheet.append([])
        sheet.append([None, "81 İl Fiyat Teklifi"])
        sheet.append([None, "İl", "İlçe", "Kamyon", "Kırkayak", "Tır"])
        sheet.append([None, "Testil", "Testil", 100, 200, 300])
        sheet.append([None, "Testil", "Testçe", 400, 500, 600])
        buffer = io.BytesIO()
        workbook.save(buffer)

        matches, _ = search_workbook(buffer.getvalue(), "Testil Testçe tır", "tasima", 8)

        self.assertEqual("Testçe", matches[0]["values"]["İlçe"])
        self.assertEqual("600 TL", matches[0]["values"]["Tır"])


if __name__ == "__main__":
    unittest.main()
