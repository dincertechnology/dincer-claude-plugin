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
        sheet.append(["İstanbul", "Ankara", 1250])
        sheet.append(["İzmir", "Bursa", 900])
        buffer = io.BytesIO()
        workbook.save(buffer)

        matches, truncated = search_workbook(
            buffer.getvalue(), "istanbul ankara", "tasima", 1
        )

        self.assertFalse(truncated)
        self.assertEqual(1, len(matches))
        self.assertEqual("1250", matches[0]["values"]["Fiyat"])


if __name__ == "__main__":
    unittest.main()
