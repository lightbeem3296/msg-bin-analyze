import tkinter as tk
from tkinter import filedialog, messagebox
import binascii
import re
import os
import traceback
from os.path import basename

def extract_text(hex_content, start_pos):
    end_pos = hex_content.find('00', start_pos * 2)
    if end_pos != -1:
        text_hex = hex_content[start_pos * 2: end_pos]
        if len(text_hex) % 2 != 0:
            text_hex = '0' + text_hex
        try:
            text = binascii.unhexlify(text_hex).decode('utf-8', errors='ignore')
            text = text.replace('\r\n', ' ').replace('\n', '\\n').replace('\r', '\\r')
            return text
        except:
            traceback.print_exc()
            return ""
    return ""


def to_little_endian(hex_str):
    little_endian_str = "".join(reversed([hex_str[i:i+2] for i in range(0, len(hex_str), 2)]))
    return little_endian_str


def extract_texts_from_file(file_path):
    ret = []
    try:
        with open(file_path, 'rb') as file:
            file_content = file.read()
        hex_cont = binascii.hexlify(file_content).decode('utf-8')

        section_count = int(hex_cont[6:8], 16)
        section_headers = []
        for i in range(section_count):
            section_headers.append(hex_cont[0x18*2 + i * 0x10*2 : 0x18*2 + (i+1) * 0x10*2])

        sec0_hdr_off = int(section_headers[0][4*2:8*2],16)
        sec0_hdr = hex_cont[sec0_hdr_off*2: (sec0_hdr_off + 12)*2]

        sec0_info_off = int(sec0_hdr[8*2:12*2],16)
        
        file_name = basename(file_path)
    
        for i in range(sec0_hdr_off, sec0_info_off, 12):
            text_hdr = hex_cont[i*2 : (i+12)*2]
            text_hdr_pos_hex = '%04x'%i

            size_hex = text_hdr[0:4]
            text_size = int(size_hex, 16)

            text_pos_hex = text_hdr[4*2 : 8*2]
            text_pos = int(text_pos_hex, 16)
            text = extract_text(hex_cont, text_pos)
            
            if text:
                overall_text_pos_hex = f"0x{text_pos_hex.upper()}"
                ret.append(f"{file_name}:{size_hex}:{overall_text_pos_hex}:{text_hdr_pos_hex}:{len(ret)+1}={text}")
            else:
                print(text)
        print(ret)
    except:
        traceback.print_exc()
    return ret


def choose_file_and_extract():
    file_path = filedialog.askopenfilename()
    if file_path:
        extracted_texts = extract_texts_from_file(file_path)
        if extracted_texts:
            output_file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                            filetypes=[("Text files", "*.txt")],
                                                            initialfile="extracted_texts.txt")

            if not output_file_path:

                return

            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                for text in extracted_texts:
                    output_file.write(text + "\n")
            messagebox.showinfo("نجاح", f"تم حفظ النتائج في {output_file_path}")
        else:
            messagebox.showinfo("نتيجة", "لم يتم استخراج أي نصوص من الملف.")
    else:
        messagebox.showinfo("إلغاء", "لم يتم اختيار ملف.")


def update_text_positions_and_sizes(original_hex_content, translated_texts_info):
    new_texts_hex = ""  # سلسلة لتخزين النصوص المترجمة في الصيغة السداسية

    for text_info in translated_texts_info:
        start_pos_hex_original, text = text_info
        start_pos_decimal_original = int(start_pos_hex_original, 16)
        translated_hex = binascii.hexlify(text.encode('utf-8')).decode('utf-8') + '00'

        new_texts_hex += translated_hex

    modified_hex_content_with_new_texts = original_hex_content + new_texts_hex
    
    return modified_hex_content_with_new_texts


def hex_to_decimal(hex_str):
    return int(hex_str, 16)


def decimal_to_hex(dec_int, padding=8):
    return hex(dec_int)[2:].zfill(padding)


def find_size_start(hex_cont):
    extracted_info = []

    section_count = int(hex_cont[6:8], 16)
    section_headers = []
    for i in range(section_count):
        section_headers.append(hex_cont[0x18*2 + i * 0x10*2 : 0x18*2 + (i+1) * 0x10*2])

    sec0_hdr_off = int(section_headers[0][4*2:8*2],16)
    sec0_hdr = hex_cont[sec0_hdr_off*2: (sec0_hdr_off + 12)*2]

    sec0_info_off = int(sec0_hdr[8*2:12*2],16)
    
    for i in range(sec0_hdr_off, sec0_info_off, 12):
        text_hdr = hex_cont[i*2 : (i+12)*2]

        size_hex = text_hdr[0:4]
        text_pos_hex = text_hdr[4*2 : 8*2]
        extracted_info.append((size_hex, text_pos_hex))

    return extracted_info


def find_or_not(original_info, translated_info):
    for trans_size, trans_position in translated_info:
        for orig_size, orig_position in original_info:
            if orig_size == trans_size and orig_position == trans_position:
                print("Match found:", orig_size, orig_position)


def update_size_with_last_bytes(original_size_hex, modified_size_hex):
    last_two_bytes_original = original_size_hex[-2:]
    return modified_size_hex[:-2] + last_two_bytes_original


def replace_texts_in_file(original_file_path, translated_file_path):
    with open(original_file_path, 'rb') as file:
        original_hex_content = binascii.hexlify(file.read()).decode('utf-8')

    original_texts_info = find_size_start(original_hex_content)
    original_file_name = os.path.basename(original_file_path)
    print(original_file_name)

    translated_texts = []
    with open(translated_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            info, text = line.strip().split('=', maxsplit=1)
            fname, original_size_hex, start_pos_hex, text_hdr_pos_hex, _ = info.split(':')
            original_size_decimal = int(original_size_hex, 16)
            start_pos_decimal = int(start_pos_hex, 16)
            translated_texts.append((fname, start_pos_decimal, text, original_size_decimal, text_hdr_pos_hex))

    new_text_start = len(original_hex_content) // 2  # حساب موقع بداية إضافة النصوص الجديدة

    for fname, start_pos_decimal, text, original_size_decimal, text_hdr_pos_hex in translated_texts:
        if fname != original_file_name:
            continue

        text_hdr_pos = int(text_hdr_pos_hex, 16)
        text_hdr2_size = int(original_hex_content[(text_hdr_pos+2)*2:(text_hdr_pos+3)*2], 16) * 0x10
        text_hdr2_pos = int(original_hex_content[(text_hdr_pos+8)*2:(text_hdr_pos+12)*2], 16)

        size_pos_list = [
            text_hdr_pos,
            text_hdr2_pos+text_hdr2_size-0xa,
            text_hdr2_pos+text_hdr2_size-0x1a,
        ]

        translated_hex = binascii.hexlify(text.encode('utf-8')).decode('utf-8') + '00'

        for original_size_hex, original_pos_hex in original_texts_info:
            original_pos_decimal = hex_to_decimal(original_pos_hex)
            if original_pos_decimal == start_pos_decimal:
                # change size field
                replacement_size_hex = '%04x'%((len(translated_hex) // 2) - 1)
                for size_pos in size_pos_list:
                    original_hex_content = original_hex_content[:(size_pos)*2] + replacement_size_hex + original_hex_content[(size_pos+2)*2:]
                
                # change pos field
                replacement_pos_hex = '%08x'%(new_text_start)
                original_hex_content = original_hex_content[:(text_hdr_pos+4)*2] + replacement_pos_hex + original_hex_content[(text_hdr_pos+8)*2:]

                # تحديث `new_text_start` لتحديد موقع البداية التالي للنص المترجم
                original_hex_content += translated_hex
                new_text_start += (len(translated_hex) // 2)

                break

    # الحفظ في ملف جديد
    new_file_path = original_file_path.replace('.msg', '_modified.msg')
    with open(new_file_path, 'wb') as new_file:
        new_file_content = binascii.unhexlify(original_hex_content)
        new_file.write(new_file_content)
    print(f"تم حفظ التغييرات في {new_file_path}")

    return new_file_path


def choose_files_and_replace_text():
    # المستخدم يختار الملف الأصلي
    original_file_path = filedialog.askopenfilename(title="اختر الملف الأصلي")
    if not original_file_path:
        return

    # المستخدم يختار الملف المترجم
    translated_file_path = filedialog.askopenfilename(title="اختر الملف المترجم")
    if not translated_file_path:
        return

        # استبدال النصوص في الملف الأصلي باستخدام الملف المترجم
    new_file_path = replace_texts_in_file(original_file_path, translated_file_path)

    # عرض رسالة نجاح إذا تم تنفيذ العملية
    if new_file_path:
        messagebox.showinfo("نجاح", f"تم استبدال النصوص بنجاح في {new_file_path}")
    else:
        messagebox.showerror("خطأ", "حدث خطأ أثناء عملية الاستبدال.")


def choose_folder_and_extract_to_one_file():
    folder_path = filedialog.askdirectory()
    if not folder_path:
        messagebox.showinfo("إلغاء", "لم يتم اختيار مجلد.")
        return

    output_file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                    filetypes=[("Text files", "*.txt")],
                                                    initialfile="extracted_texts_all.txt")
    if not output_file_path:
        messagebox.showinfo("إلغاء", "لم يتم تحديد مسار للحفظ.")
        return

    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        for subdir, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(subdir, file)
                extracted_texts = extract_texts_from_file(file_path)
                for text in extracted_texts:
                    output_file.write(text + "\n")

    messagebox.showinfo("نجاح", f"تم حفظ النتائج في {output_file_path}")


def choose_folder_and_replace_texts():
    original_folder_path = filedialog.askdirectory(title="اختر المجلد الأصلي")
    if not original_folder_path:
        return

    translated_file_path = filedialog.askopenfilename(title="اختر الملف المترجم")
    if not translated_file_path:
        return

    for subdir, dirs, files in os.walk(original_folder_path):
        for file in files:
            if not file.lower().endswith('.msg'):
                continue

            file_path = os.path.join(subdir, file)
            if os.path.isfile(file_path):
                new_file_path = replace_texts_in_file(file_path, translated_file_path)

    messagebox.showinfo("نجاح", "تم استبدال النصوص بنجاح.")


def test():
    print(extract_texts_from_file(r'D:\work\New folder\uid00xxxxxx\uid000c147e - Copy.msg'))


def main_gui():
    root = tk.Tk()
    root.title("Extractor")

    btn_extract = tk.Button(root, text="اختر مجلد واستخرج النصوص", command=choose_folder_and_extract_to_one_file)
    btn_extract.pack(pady=20)

    # Similarly, ensure btn_replace is defined before it's used.
    btn_replace = tk.Button(root, text="استبدال النصوص في مجلد", command=choose_folder_and_replace_texts)
    btn_replace.pack(pady=20)

    btn_extract1 = tk.Button(root, text="اختر ملف واستخرج النصوص", command=choose_file_and_extract)
    btn_extract1.pack(pady=20)

    # إضافة زر جديد لواجهة المستخدم لاستبدال النصوص المترجمة
    btn_replace1 = tk.Button(root, text="استبدال النصوص المترجمة", command=choose_files_and_replace_text)
    btn_replace1.pack(pady=20)

    root.mainloop()
# فقط عندما يكون البرنامج هو النقطة الرئيسية للتنفيذ
if __name__ == "__main__":
    main_gui()
    # test()
                                                                                                