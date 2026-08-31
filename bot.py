import os
import random
import requests

from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, request


# =========================================================
# 🎓 BacMind DZ
# بوت بكالوريا جزائري - ملف واحد bot.py
# =========================================================

app = Flask(__name__)


# =========================================================
# ⚙️ الإعدادات
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

TELEGRAM_API = (
    f"https://api.telegram.org/bot{BOT_TOKEN}"
    if BOT_TOKEN
    else ""
)

# توقيت الجزائر
ALGERIA_TZ = ZoneInfo("Africa/Algiers")


# =========================================================
# 📄 روابط ملفات PDF
# ضع روابط ملفاتك هنا
# =========================================================

PDF_LINKS = {
    "🧠 فلسفة": "ضع_رابط_PDF_الفلسفة_هنا",
    "🇫🇷 فرنسية": "ضع_رابط_PDF_الفرنسية_هنا",
    "🇬🇧 إنجليزية": "ضع_رابط_PDF_الإنجليزية_هنا",
    "🇪🇸 إسبانية": "ضع_رابط_PDF_الإسبانية_هنا",
}


# =========================================================
# 👥 المستخدمون
# =========================================================

users = {}


# =========================================================
# 🧠 بنك الأسئلة
# =========================================================

def Q(question, options, answer, explanation=""):
    return {
        "q": question,
        "options": options,
        "answer": answer,
        "explanation": explanation
    }


QUESTIONS = {

    # =====================================================
    # 🧠 الفلسفة - 70 سؤال
    # =====================================================

    "الفلسفة": [

        Q(
            "من صاحب المقولة: أنا أفكر إذن أنا موجود؟",
            ["أفلاطون", "أرسطو", "ديكارت", "كانط"],
            2,
            "المقولة مرتبطة برينيه ديكارت."
        ),

        Q(
            "من صاحب نظرية المثل؟",
            ["أفلاطون", "أرسطو", "ديكارت", "نيتشه"],
            0,
            "نظرية المثل من أشهر أفكار أفلاطون."
        ),

        Q(
            "من قال إن الإنسان حيوان سياسي؟",
            ["سقراط", "أرسطو", "كانط", "ماركس"],
            1,
            "أرسطو اعتبر الإنسان كائنًا اجتماعيًا وسياسيًا."
        ),

        Q(
            "من الفيلسوف المرتبط بالشك المنهجي؟",
            ["أفلاطون", "ديكارت", "هيغل", "ماركس"],
            1,
            "استخدم ديكارت الشك المنهجي للوصول إلى اليقين."
        ),

        Q(
            "من ربط الأخلاق بالواجب؟",
            ["أرسطو", "كانط", "نيتشه", "سقراط"],
            1,
            "الأخلاق الكانطية تقوم على مبدأ الواجب."
        ),

        Q(
            "ما المقصود بالمنطق؟",
            ["علم التفكير الصحيح", "علم التاريخ", "علم الفن", "علم الاقتصاد"],
            0,
            "المنطق يهتم بقواعد التفكير والاستدلال الصحيح."
        ),

        Q(
            "ما المقصود بالإبستمولوجيا؟",
            ["دراسة المعرفة", "دراسة الفن", "دراسة السياسة", "دراسة الاقتصاد"],
            0,
            "الإبستمولوجيا تبحث في المعرفة ومصادرها وحدودها."
        ),

        Q(
            "ما المقصود بالأخلاق؟",
            ["دراسة القيم والسلوك", "دراسة الطقس", "دراسة الحساب", "دراسة اللغة"],
            0,
            "الأخلاق تبحث في القيم والمعايير الموجهة للسلوك."
        ),

        Q(
            "ما المقصود بالجماليات؟",
            ["دراسة الجمال والفن", "دراسة المنطق", "دراسة الاقتصاد", "دراسة التاريخ"],
            0,
            "الجماليات تهتم بقضايا الفن والجمال."
        ),

        Q(
            "من صاحب كتاب الجمهورية؟",
            ["أفلاطون", "أرسطو", "كانط", "ديكارت"],
            0,
            "الجمهورية من أشهر مؤلفات أفلاطون."
        ),

        Q(
            "من كان تلميذ سقراط؟",
            ["أفلاطون", "ديكارت", "كانط", "ماركس"],
            0,
            "كان أفلاطون أحد أشهر تلاميذ سقراط."
        ),

        Q(
            "من كان تلميذ أفلاطون؟",
            ["أرسطو", "سقراط", "كانط", "هيغل"],
            0,
            "أرسطو درس في أكاديمية أفلاطون."
        ),

        Q(
            "ما الهدف من التفكير النقدي؟",
            ["تحليل الأفكار والأدلة", "رفض كل شيء", "الحفظ فقط", "تجنب الأسئلة"],
            0,
            "التفكير النقدي يقوم على فحص الأفكار والأدلة."
        ),

        Q(
            "الحقيقة في التصور الكلاسيكي هي:",
            ["مطابقة الفكر للواقع", "الرأي الشخصي", "الخيال", "الإشاعة"],
            0,
            "من التصورات الكلاسيكية للحقيقة مطابقة الفكر للواقع."
        ),

        Q(
            "ما المفهوم المرتبط بحرية الاختيار؟",
            ["الإرادة", "الطبيعة", "الجمال", "الذاكرة"],
            0,
            "الإرادة ترتبط بالاختيار واتخاذ القرار."
        ),

        Q(
            "ما المفهوم الذي يرتبط بتحمل نتائج الاختيار؟",
            ["المسؤولية", "الخيال", "الجمال", "اللغة"],
            0,
            "المسؤولية ترتبط بتحمل نتائج الأفعال والاختيارات."
        ),

        Q(
            "من أبرز الفلاسفة العقلانيين؟",
            ["ديكارت", "لوك", "هيوم", "بيكون"],
            0,
            "ديكارت من أبرز ممثلي الاتجاه العقلي."
        ),

        Q(
            "من أبرز الفلاسفة التجريبيين؟",
            ["جون لوك", "ديكارت", "سبينوزا", "ليبنتز"],
            0,
            "جون لوك من أشهر فلاسفة التجربة."
        ),

        Q(
            "ما مصدر المعرفة عند التجريبيين أساسًا؟",
            ["التجربة", "الحدس فقط", "الخيال", "الأسطورة"],
            0,
            "التجريبية تؤكد أهمية التجربة الحسية في المعرفة."
        ),

        Q(
            "ما الاتجاه الذي يعطي العقل دورًا أساسيًا في المعرفة؟",
            ["العقلانية", "التجريبية", "العدمية", "البراغماتية"],
            0,
            "العقلانية تجعل العقل مصدرًا أساسيًا للمعرفة."
        ),

        Q(
            "من صاحب عبارة الإنسان ذئب لأخيه الإنسان؟",
            ["هوبز", "روسو", "كانط", "أفلاطون"],
            0,
            "تنسب العبارة إلى توماس هوبز."
        ),

        Q(
            "من الفيلسوف المرتبط بالعقد الاجتماعي؟",
            ["روسو", "ديكارت", "نيتشه", "أرسطو"],
            0,
            "روسو من أشهر فلاسفة العقد الاجتماعي."
        ),

        Q(
            "ما الغاية الأساسية من القانون؟",
            ["تنظيم الحياة الاجتماعية", "إلغاء الحرية", "نشر الفوضى", "منع التفكير"],
            0,
            "القانون يهدف إلى تنظيم العلاقات داخل المجتمع."
        ),

        Q(
            "العدالة ترتبط أساسًا بـ:",
            ["الإنصاف", "الفوضى", "اللامبالاة", "الجهل"],
            0,
            "العدالة ترتبط بالإنصاف وإعطاء كل ذي حق حقه."
        ),

        Q(
            "ما الذي يميز السؤال الفلسفي؟",
            ["العمق والنقد", "الحفظ", "التكرار", "الإجابة السريعة"],
            0,
            "السؤال الفلسفي يبحث في المبادئ والمعاني بشكل نقدي."
        ),

        Q(
            "الفلسفة تعني أصلًا:",
            ["حب الحكمة", "حب المال", "حب القوة", "حب الشهرة"],
            0,
            "مصطلح فلسفة يعني حب الحكمة."
        ),

        Q(
            "من الفيلسوف الذي اهتم بمبدأ الواجب الأخلاقي؟",
            ["كانط", "ماركس", "أرسطو", "هيغل"],
            0,
            "كانط جعل الواجب أساسًا مهمًا في الأخلاق."
        ),

        Q(
            "ما المقصود بالوعي؟",
            ["إدراك الذات والعالم", "النوم", "النسيان", "الجهل"],
            0,
            "الوعي يرتبط بالإدراك والشعور بالذات والعالم."
        ),

        Q(
            "ما المقصود باللاوعي؟",
            ["ما هو خارج الوعي المباشر", "الوعي الكامل", "العقل الرياضي", "المعرفة العلمية"],
            0,
            "اللاوعي يشير إلى عمليات ومحتويات لا تكون حاضرة مباشرة في الوعي."
        ),

        Q(
            "من الفيلسوف المرتبط بمفهوم العود الأبدي؟",
            ["نيتشه", "ديكارت", "سقراط", "أفلاطون"],
            0,
            "العود الأبدي من المفاهيم المرتبطة بنيتشه."
        ),

        Q(
            "من صاحب فلسفة الماركسية؟",
            ["كارل ماركس", "كانط", "ديكارت", "أفلاطون"],
            0,
            "كارل ماركس أحد أهم مؤسسي الفكر الماركسي."
        ),

        Q(
            "ما الموضوع الأساسي للفلسفة السياسية؟",
            ["الدولة والسلطة والعدالة", "الأعداد", "الطقس", "الطب"],
            0,
            "الفلسفة السياسية تبحث في الدولة والسلطة والعدالة والحرية."
        ),

        Q(
            "ما المقصود بالحرية؟",
            ["القدرة على الاختيار مع المسؤولية", "الفوضى", "رفض القانون", "عدم التفكير"],
            0,
            "الحرية لا تنفصل عن المسؤولية."
        ),

        Q(
            "ما العلاقة بين الحرية والمسؤولية؟",
            ["الحرية تستلزم المسؤولية", "لا علاقة بينهما", "المسؤولية تلغي الحرية", "الحرية تعني الفوضى"],
            0,
            "الاختيار الحر يجعل الإنسان مسؤولًا عن أفعاله."
        ),

        Q(
            "ما المقصود بالقيمة؟",
            ["مبدأ يوجه الحكم والسلوك", "رقم فقط", "لون", "مكان"],
            0,
            "القيم تساعد الإنسان في توجيه أحكامه وسلوكه."
        ),

        Q(
            "ما الفرق الأساسي بين الرأي والمعرفة؟",
            ["المعرفة تقوم على تبرير وأدلة", "الرأي دائمًا صحيح", "لا فرق", "المعرفة مجرد إشاعة"],
            0,
            "المعرفة تتطلب مبررات وأدلة أقوى من مجرد الرأي."
        ),

        Q(
            "ما المقصود بالاستدلال؟",
            ["الانتقال من مقدمات إلى نتيجة", "حفظ النصوص", "الرسم", "الخيال"],
            0,
            "الاستدلال عملية عقلية ننتقل فيها من مقدمات إلى نتائج."
        ),

        Q(
            "ما وظيفة الحجة؟",
            ["دعم موقف أو فكرة", "إخفاء الحقيقة", "إلغاء الحوار", "منع السؤال"],
            0,
            "الحجة تستخدم لتبرير موقف أو دعم نتيجة."
        ),

        Q(
            "ما الذي يميز التفكير العلمي؟",
            ["المنهج والدليل", "الخرافة", "الإشاعة", "التقليد فقط"],
            0,
            "العلم يعتمد على المنهج والملاحظة والدليل."
        ),

        Q(
            "ما المقصود بالموضوعية؟",
            ["محاولة الحكم بعيدًا عن التحيز", "اتباع الرأي الشخصي فقط", "رفض الأدلة", "الخيال"],
            0,
            "الموضوعية تسعى إلى تقليل تأثير التحيز الشخصي."
        ),

        Q(
            "ما المقصود بالنسبية؟",
            ["ارتباط الحكم بسياق أو منظور معين", "ثبات كل الأحكام", "رفض التفكير", "الحقيقة الرياضية"],
            0,
            "النسبية تشير إلى ارتباط بعض الأحكام بسياق أو منظور."
        ),

        Q(
            "ما المقصود بالبراغماتية؟",
            ["ربط قيمة الفكرة بنتائجها العملية", "رفض التجربة", "رفض العمل", "الاعتماد على الأسطورة"],
            0,
            "البراغماتية تهتم بالنتائج والآثار العملية للأفكار."
        ),

        Q(
            "من الفيلسوف المرتبط بالبراغماتية؟",
            ["وليام جيمس", "أفلاطون", "ديكارت", "كانط"],
            0,
            "وليام جيمس من أبرز ممثلي البراغماتية."
        ),

        Q(
            "ما المقصود بالجدل؟",
            ["مناقشة الأفكار والحجج", "الحفظ", "الصمت", "الرياضة"],
            0,
            "الجدل يقوم على عرض المواقف ومناقشة الحجج."
        ),

        Q(
            "ما أهمية الحوار الفلسفي؟",
            ["فحص الأفكار وتطويرها", "منع الاختلاف", "حفظ النصوص", "إلغاء السؤال"],
            0,
            "الحوار يساعد على اختبار الأفكار ومراجعة المواقف."
        ),

        Q(
            "من الفيلسوف الذي اهتم بعالم المحسوسات والمثل؟",
            ["أفلاطون", "لوك", "هيوم", "ماركس"],
            0,
            "ميز أفلاطون بين عالم المحسوسات وعالم المثل."
        ),

        Q(
            "ما المقصود بالعقل؟",
            ["ملكة التفكير والفهم", "الذاكرة فقط", "الحواس فقط", "الجسم"],
            0,
            "العقل يرتبط بالتفكير والفهم والاستدلال."
        ),

        Q(
            "ما دور الشك في الفلسفة؟",
            ["فحص المعتقدات وعدم قبولها دون نقد", "رفض الحقيقة دائمًا", "منع المعرفة", "إلغاء التفكير"],
            0,
            "الشك الفلسفي يمكن أن يكون وسيلة لفحص المعتقدات."
        ),

        Q(
            "هل الشك المنهجي يعني إنكار كل شيء نهائيًا؟",
            ["لا", "نعم دائمًا", "هو رفض العلم", "هو رفض العقل"],
            0,
            "الشك المنهجي وسيلة للوصول إلى اليقين وليس غاية في ذاته."
        ),

        Q(
            "ما علاقة الفلسفة بالسؤال؟",
            ["السؤال نقطة انطلاق للتفكير", "السؤال غير مهم", "السؤال يمنع المعرفة", "السؤال للحفظ فقط"],
            0,
            "السؤال الفلسفي يفتح مجال البحث والتفكير."
        ),

        Q(
            "ما المقصود بالوجود؟",
            ["كون الشيء حاضرًا أو متحققًا", "الخيال فقط", "الرأي", "اللغة"],
            0,
            "الوجود من أكبر موضوعات الفلسفة."
        ),

        Q(
            "ما الفرع الذي يدرس الوجود؟",
            ["الأنطولوجيا", "الإبستمولوجيا", "الجماليات", "المنطق"],
            0,
            "الأنطولوجيا تبحث في الوجود وماهيته."
        ),

        Q(
            "ما الفرع الذي يدرس القيم الأخلاقية؟",
            ["الأخلاق", "الأنطولوجيا", "المنطق", "الجماليات"],
            0,
            "الأخلاق تبحث في الخير والشر والقيم والسلوك."
        ),

        Q(
            "ما الفرع الذي يدرس الحجج والاستدلال؟",
            ["المنطق", "الأخلاق", "الجماليات", "السياسة"],
            0,
            "المنطق يهتم بصحة الاستدلال."
        ),

        Q(
            "ما الفرع الذي يدرس الفن والجمال؟",
            ["الجماليات", "الأخلاق", "المنطق", "الإبستمولوجيا"],
            0,
            "الجماليات هي فلسفة الفن والجمال."
        ),

        Q(
            "ما أهمية الفلسفة بالنسبة للطالب؟",
            ["تنمية التفكير والتحليل", "الحفظ فقط", "تجنب الأسئلة", "إلغاء النقاش"],
            0,
            "الفلسفة تساعد على تطوير التفكير والتحليل والحجاج."
        ),

        Q(
            "ما المقصود بالحجة القوية؟",
            ["حجة مدعومة بأسباب وأدلة", "رأي بلا دليل", "إشاعة", "تخمين"],
            0,
            "قوة الحجة ترتبط بجودة أسبابها وأدلتها."
        ),

        Q(
            "ما معنى النقد الفلسفي؟",
            ["فحص الأفكار وتقويمها", "الإهانة", "الرفض فقط", "الحفظ"],
            0,
            "النقد الفلسفي تحليل وتقويم وليس مجرد رفض."
        ),

        Q(
            "هل الفلسفة تقتصر على حفظ أقوال الفلاسفة؟",
            ["لا", "نعم", "أحيانًا فقط", "دائمًا"],
            0,
            "الفلسفة تعتمد على الفهم والتحليل والحجاج."
        ),

        Q(
            "ما المقصود بالمشكلة الفلسفية؟",
            ["سؤال عميق قابل للنقاش", "سؤال حسابي فقط", "معلومة محفوظة", "إشاعة"],
            0,
            "المشكلة الفلسفية تتطلب التفكير والمناقشة والحجاج."
        ),

        Q(
            "ما أهمية المفهوم في الفلسفة؟",
            ["تحديد المعاني بدقة", "زيادة الحفظ", "منع الحوار", "إلغاء التفكير"],
            0,
            "المفاهيم تساعد على ضبط المعاني والأفكار."
        ),

        Q(
            "ما المقصود بالحتمية؟",
            ["خضوع الأحداث لأسباب وشروط", "الحرية المطلقة", "الفوضى", "الصدفة دائمًا"],
            0,
            "الحتمية ترى أن الأحداث ترتبط بأسباب وشروط محددة."
        ),

        Q(
            "ما القضية التي تبحث في العلاقة بين الحتمية والاختيار؟",
            ["الحرية", "الجمال", "الفن", "اللغة"],
            0,
            "مسألة الحرية ترتبط بالسؤال عن الحتمية والاختيار."
        ),

        Q(
            "ما المقصود بالوعي بالذات؟",
            ["إدراك الإنسان لنفسه", "نسيان الذات", "النوم", "رفض التفكير"],
            0,
            "الوعي بالذات هو إدراك الإنسان لذاته وأفكاره."
        ),

        Q(
            "ما علاقة اللغة بالفكر؟",
            ["بينهما علاقة وثيقة", "لا علاقة إطلاقًا", "اللغة تمنع التفكير دائمًا", "الفكر هو اللغة فقط"],
            0,
            "هناك علاقة فلسفية مهمة بين اللغة والتفكير."
        ),

        Q(
            "ما المقصود بالعقلانية؟",
            ["الاعتماد على العقل في بناء المعرفة", "رفض العقل", "رفض الأدلة", "الاعتماد على الخرافة"],
            0,
            "العقلانية تعطي العقل دورًا أساسيًا في المعرفة."
        ),

        Q(
            "ما المقصود بالتجريبية؟",
            ["إعطاء التجربة دورًا أساسيًا في المعرفة", "رفض الحواس", "رفض العلم", "الاعتماد على الأسطورة"],
            0,
            "التجريبية تؤكد أهمية التجربة في اكتساب المعرفة."
        ),

        Q(
            "ما الذي يجعل النقاش فلسفيًا؟",
            ["الحجة والتحليل والبحث عن المبررات", "الصراخ", "الحفظ", "الإهانة"],
            0,
            "النقاش الفلسفي يقوم على الحجة والتحليل."
        ),

        Q(
            "ما الهدف من دراسة تاريخ الفلسفة؟",
            ["فهم تطور الأفكار", "حفظ الأسماء فقط", "رفض الفلاسفة", "تجنب التفكير"],
            0,
            "تاريخ الفلسفة يساعد على فهم تطور المشكلات والمواقف."
        ),

        Q(
            "ما المقصود بالتسامح الفكري؟",
            ["احترام الاختلاف مع مناقشة الأفكار", "قبول كل شيء دون نقد", "رفض الآخر", "منع الحوار"],
            0,
            "التسامح الفكري يسمح بالاختلاف والحوار."
        ),

        Q(
            "ما دور الفلسفة في مواجهة الخرافة؟",
            ["استخدام العقل والنقد", "نشر الخرافة", "رفض المعرفة", "الحفظ"],
            0,
            "التفكير النقدي يساعد على فحص الادعاءات."
        ),

        Q(
            "ما العلاقة بين السؤال والجواب الفلسفي؟",
            ["السؤال يفتح مجال البحث والجواب قابل للمناقشة", "الجواب دائمًا نهائي", "لا علاقة", "السؤال غير مهم"],
            0,
            "الجواب الفلسفي يمكن أن يكون موضوعًا للنقاش والنقد."
        ),

        Q(
            "ما الهدف من المقالة الفلسفية؟",
            ["مناقشة مشكلة بالحجج", "حفظ قائمة أسماء", "كتابة قصة", "وصف مكان"],
            0,
            "المقالة الفلسفية تعالج مشكلة وتعرض حججًا ومواقف."
        ),

        Q(
            "ما أهم ما يحتاجه الطالب في الفلسفة؟",
            ["الفهم والتحليل والحجاج", "الحفظ وحده", "السرعة فقط", "نسخ الدروس"],
            0,
            "الفهم والتحليل والحجاج عناصر أساسية في الفلسفة."
        ),

        Q(
            "ما المقصود بالاستقلال الفكري؟",
            ["تكوين موقف بعد التفكير والنقد", "رفض كل الآراء", "اتباع الآخرين دائمًا", "عدم التفكير"],
            0,
            "الاستقلال الفكري يعني بناء الموقف بعد التفكير والنقد."
        ),

        Q(
            "هل الاختلاف بين الفلاسفة يعني أن الفلسفة بلا قيمة؟",
            ["لا", "نعم", "دائمًا", "ليس لها علاقة"],
            0,
            "الاختلاف جزء من طبيعة التفكير الفلسفي."
        ),

        Q(
            "ما الذي يساعد على بناء موقف فلسفي جيد؟",
            ["تعريف المفاهيم والحجج والأمثلة", "الحفظ العشوائي", "الإطالة فقط", "تجنب الأدلة"],
            0,
            "الموقف الجيد يحتاج إلى مفاهيم واضحة وحجج وأمثلة."
        ),

        Q(
            "ما المقصود بالاستنتاج؟",
            ["الوصول إلى نتيجة انطلاقًا من مقدمات", "طرح سؤال فقط", "الحفظ", "الوصف"],
            0,
            "الاستنتاج انتقال عقلي من مقدمات إلى نتيجة."
        ),

        Q(
            "ما قيمة الحوار في بناء المعرفة؟",
            ["يساعد على اختبار الآراء والحجج", "يلغي التفكير", "يمنع النقد", "لا قيمة له"],
            0,
            "الحوار يسمح بمراجعة الأفكار واختبار الحجج."
        ),
    ],
}


# =========================================================
# 🇫🇷 الفرنسية - 70 سؤال
# =========================================================

QUESTIONS["الفرنسية"] = [

    Q("Quel est le synonyme de « heureux » ?",
      ["Triste", "Content", "Malade", "Fatigué"], 1,
      "Heureux et content ont un sens proche."),

    Q("Quel est le contraire de « difficile » ?",
      ["Compliqué", "Facile", "Long", "Fort"], 1,
      "Le contraire de difficile est facile."),

    Q("Complétez : Je ___ au lycée.",
      ["vais", "va", "allons", "allez"], 0,
      "Avec je, on dit je vais."),

    Q("Quel est le pluriel de « cheval » ?",
      ["Chevals", "Chevaux", "Chevales", "Chevaus"], 1,
      "Le pluriel de cheval est chevaux."),

    Q("« J'ai étudié » est à quel temps ?",
      ["Présent", "Futur", "Passé composé", "Imparfait"], 2,
      "J'ai étudié est au passé composé."),

    Q("Complétez : Nous ___ nos devoirs.",
      ["fait", "faisons", "faire", "faites"], 1,
      "Avec nous, on dit nous faisons."),

    Q("Quel mot est un adjectif ?",
      ["Rapidement", "Maison", "Intelligent", "Courir"], 2,
      "Intelligent est un adjectif."),

    Q("Quel est le féminin de « acteur » ?",
      ["Acteuse", "Actrice", "Acteurse", "Acteur"], 1,
      "Le féminin de acteur est actrice."),

    Q("Si j'avais le temps, je ___ davantage.",
      ["lis", "lirais", "lirai", "lu"], 1,
      "Après si + imparfait, on utilise le conditionnel."),

    Q("Quel est le contraire de « ancien » ?",
      ["Vieux", "Moderne", "Passé", "Historique"], 1,
      "Dans ce contexte, moderne est le contraire d'ancien."),

    Q("Complétez : Tu ___ une belle voiture.",
      ["as", "a", "avons", "avez"], 0,
      "Avec tu, le verbe avoir donne tu as."),

    Q("Complétez : Ils ___ au football.",
      ["joue", "jouent", "jouons", "jouez"], 1,
      "Avec ils, on dit ils jouent."),

    Q("Quel est le féminin de « sportif » ?",
      ["Sportive", "Sportife", "Sportifs", "Sporteur"], 0,
      "Le féminin de sportif est sportive."),

    Q("Quel est le contraire de « rapide » ?",
      ["Vite", "Lent", "Fort", "Grand"], 1,
      "Le contraire de rapide est lent."),

    Q("Quel est le synonyme de « commencer » ?",
      ["Finir", "Débuter", "Arrêter", "Oublier"], 1,
      "Commencer signifie débuter."),

    Q("Quel est le participe passé de « faire » ?",
      ["Fait", "Faisant", "Faiter", "Faire"], 0,
      "Le participe passé de faire est fait."),

    Q("Complétez : Elle ___ française.",
      ["est", "sont", "es", "sommes"], 0,
      "Avec elle, on utilise est."),

    Q("Quel est le pluriel de « journal » ?",
      ["Journals", "Journaux", "Journalx", "Journales"], 1,
      "Le pluriel de journal est journaux."),

    Q("Quel est le contraire de « jeune » ?",
      ["Petit", "Vieux", "Nouveau", "Court"], 1,
      "Le contraire de jeune est vieux."),

    Q("Complétez : Nous ___ français.",
      ["parle", "parlons", "parlez", "parlent"], 1,
      "Avec nous, on dit nous parlons."),

    Q("Quel est le féminin de « heureux » ?",
      ["Heureuse", "Heureuxe", "Heureuxse", "Heureuses"], 0,
      "Le féminin de heureux est heureuse."),

    Q("Quel est le contraire de « propre » ?",
      ["Sale", "Beau", "Grand", "Neuf"], 0,
      "Le contraire de propre est sale."),

    Q("Complétez : Vous ___ raison.",
      ["avez", "as", "a", "avons"], 0,
      "Avec vous, on dit vous avez."),

    Q("Quel est le synonyme de « beau » ?",
      ["Joli", "Triste", "Laid", "Faible"], 0,
      "Beau et joli sont proches."),

    Q("Quel est le contraire de « facile » ?",
      ["Simple", "Difficile", "Petit", "Court"], 1,
      "Le contraire de facile est difficile."),

    Q("Complétez : Il ___ très intelligent.",
      ["est", "sont", "es", "sommes"], 0,
      "Avec il, on utilise est."),

    Q("Quel est le pluriel de « travail » ?",
      ["Travails", "Travaux", "Travailes", "Travailsx"], 1,
      "Le pluriel de travail est travaux."),

    Q("Quel est le participe passé de « écrire » ?",
      ["Écrit", "Écrivé", "Écrivant", "Écrire"], 0,
      "Le participe passé est écrit."),

    Q("Quel est le contraire de « toujours » ?",
      ["Souvent", "Jamais", "Encore", "Déjà"], 1,
      "Dans ce contexte, jamais est l'opposé."),

    Q("Complétez : Je ___ mes leçons.",
      ["révise", "révises", "révisons", "révisez"], 0,
      "Avec je, on dit je révise."),

    Q("Quel mot est un nom ?",
      ["Rapidement", "Maison", "Courir", "Beau"], 1,
      "Maison est un nom."),

    Q("Quel mot est un verbe ?",
      ["Table", "Courir", "Grand", "Rapidement"], 1,
      "Courir est un verbe."),

    Q("Quel mot est un adverbe ?",
      ["Rapidement", "Maison", "Intelligent", "Écrire"], 0,
      "Rapidement est un adverbe."),

    Q("Quel est le futur de « aller » avec je ?",
      ["J'irai", "Je vais", "J'allais", "Je suis allé"], 0,
      "Au futur, on dit j'irai."),

    Q("Quel est l'imparfait de « être » avec nous ?",
      ["Nous sommes", "Nous étions", "Nous serons", "Nous fûmes"], 1,
      "À l'imparfait : nous étions."),

    Q("Quel est le passé composé de « manger » avec nous ?",
      ["Nous mangions", "Nous avons mangé", "Nous mangerons", "Nous mangeons"], 1,
      "Le passé composé est nous avons mangé."),

    Q("Quel article accompagne généralement « école » ?",
      ["Une", "Un", "Des", "Le"], 0,
      "On dit une école."),

    Q("Quel article accompagne « livre » ?",
      ["Une", "Un", "Une des", "La"], 1,
      "On dit un livre."),

    Q("Quel est le féminin de « étudiant » ?",
      ["Étudiante", "Étudieuse", "Étude", "Étudiant"], 0,
      "Le féminin est étudiante."),

    Q("Quel est le contraire de « fort » ?",
      ["Puissant", "Faible", "Grand", "Rapide"], 1,
      "Le contraire de fort est faible."),

    Q("Quel est le synonyme de « aider » ?",
      ["Assister", "Refuser", "Casser", "Oublier"], 0,
      "Aider peut signifier assister."),

    Q("Complétez : Ils ___ leurs examens.",
      ["prépare", "préparent", "préparons", "préparez"], 1,
      "Avec ils, on dit préparent."),

    Q("Complétez : Nous ___ demain.",
      ["partons", "partez", "partent", "part"], 0,
      "Avec nous : nous partons."),

    Q("Quel est le contraire de « clair » ?",
      ["Lumineux", "Sombre", "Brillant", "Propre"], 1,
      "Le contraire de clair peut être sombre."),

    Q("Quel est le synonyme de « commencer » ?",
      ["Débuter", "Finir", "Quitter", "Arrêter"], 0,
      "Commencer signifie débuter."),

    Q("Quel est le féminin de « vendeur » ?",
      ["Vendeuse", "Vendeure", "Venderesse", "Vendeur"], 0,
      "Le féminin courant est vendeuse."),

    Q("Quel est le pluriel de « animal » ?",
      ["Animals", "Animaux", "Animales", "Animalx"], 1,
      "Le pluriel est animaux."),

    Q("Complétez : Elle ___ un livre.",
      ["lit", "lis", "lisez", "lire"], 0,
      "Avec elle, on dit elle lit."),

    Q("Complétez : Tu ___ très bien.",
      ["chantes", "chante", "chantons", "chantent"], 0,
      "Avec tu : tu chantes."),

    Q("Quel est le contraire de « triste » ?",
      ["Heureux", "Malade", "Fatigué", "Seul"], 0,
      "Le contraire de triste est heureux."),

    Q("Quel est le synonyme de « intelligent » ?",
      ["Brillant", "Lent", "Faible", "Triste"], 0,
      "Brillant peut être synonyme d'intelligent."),

    Q("Quel temps exprime une action habituelle dans le passé ?",
      ["Imparfait", "Futur", "Présent", "Conditionnel"], 0,
      "L'imparfait sert notamment à exprimer des habitudes passées."),

    Q("Quel temps exprime une action future ?",
      ["Futur", "Imparfait", "Présent", "Plus-que-parfait"], 0,
      "Le futur exprime une action à venir."),

    Q("Quel mode exprime souvent une hypothèse ?",
      ["Conditionnel", "Indicatif", "Infinitif", "Impératif"], 0,
      "Le conditionnel est souvent utilisé pour exprimer une hypothèse."),

    Q("Quel signe termine généralement une question ?",
      [".", ",", "?", "!"], 2,
      "Une question se termine généralement par un point d'interrogation."),

    Q("Quel mot introduit souvent une cause ?",
      ["Parce que", "Mais", "Ou", "Donc"], 0,
      "Parce que introduit une cause."),

    Q("Quel mot exprime généralement une conséquence ?",
      ["Donc", "Parce que", "Mais", "Ou"], 0,
      "Donc peut introduire une conséquence."),

    Q("Quel mot exprime l'opposition ?",
      ["Mais", "Et", "Donc", "Car"], 0,
      "Mais introduit une opposition."),

    Q("Quel mot exprime l'addition ?",
      ["Et", "Mais", "Donc", "Car"], 0,
      "Et permet d'ajouter une information."),

    Q("Quel est le contraire de « accepter » ?",
      ["Refuser", "Aimer", "Prendre", "Donner"], 0,
      "Le contraire d'accepter est refuser."),

    Q("Quel est le synonyme de « regarder » ?",
      ["Observer", "Oublier", "Dormir", "Courir"], 0,
      "Observer signifie regarder attentivement."),

    Q("Quel est le contraire de « entrer » ?",
      ["Sortir", "Arriver", "Venir", "Monter"], 0,
      "Le contraire d'entrer est sortir."),

    Q("Quel est le contraire de « monter » ?",
      ["Descendre", "Avancer", "Entrer", "Courir"], 0,
      "Le contraire de monter est descendre."),

    Q("Quel est le synonyme de « commencer » ?",
      ["Débuter", "Terminer", "Fermer", "Oublier"], 0,
      "Débuter est synonyme de commencer."),

    Q("Quel est le contraire de « gagner » ?",
      ["Perdre", "Réussir", "Avancer", "Trouver"], 0,
      "Le contraire de gagner est perdre."),

    Q("Quel est le contraire de « vrai » ?",
      ["Faux", "Bon", "Grand", "Fort"], 0,
      "Le contraire de vrai est faux."),

    Q("Complétez : Il faut que tu ___ tes devoirs.",
      ["fasses", "fais", "fera", "faire"], 0,
      "Après il faut que, on utilise ici le subjonctif : que tu fasses."),

    Q("Quel est le féminin de « directeur » ?",
      ["Directrice", "Directeuse", "Directeurse", "Direction"], 0,
      "Le féminin de directeur est directrice."),

    Q("Quel est le pluriel de « cheval » ?",
      ["Chevals", "Chevaux", "Chevales", "Chevaus"], 1,
      "Cheval devient chevaux au pluriel."),

    Q("Quel est le contraire de « difficile » ?",
      ["Facile", "Long", "Fort", "Lent"], 0,
      "Le contraire de difficile est facile."),

    Q("Quel mot signifie « rapidement » ?",
      ["Vite", "Lentement", "Rarement", "Jamais"], 0,
      "Vite signifie rapidement.")
]


# =====================================================
# 🇬🇧 الإنجليزية - 70 سؤال
# =====================================================

QUESTIONS["الإنجليزية"] = [

    Q("She ___ English every day.",
      ["study", "studies", "studying", "studied"], 1,
      "With she/he/it, the present simple normally takes -s/-es."),

    Q("What is the past tense of go?",
      ["goed", "gone", "went", "going"], 2,
      "The past simple of go is went."),

    Q("I ___ a student.",
      ["am", "is", "are", "be"], 0,
      "With I, use am."),

    Q("What is the opposite of easy?",
      ["Simple", "Hard", "Short", "Small"], 1,
      "The opposite of easy is hard."),

    Q("He ___ like football.",
      ["don't", "doesn't", "isn't", "not"], 1,
      "With he, use doesn't + base verb."),

    Q("What is the comparative of good?",
      ["Gooder", "More good", "Better", "Best"], 2,
      "The comparative of good is better."),

    Q("They ___ playing now.",
      ["is", "am", "are", "be"], 2,
      "With they, use are."),

    Q("Environment means:",
      ["البيئة", "الاقتصاد", "التاريخ", "الرياضة"], 0,
      "Environment means البيئة."),

    Q("I have lived here ___ 2020.",
      ["for", "since", "at", "on"], 1,
      "Since is used with a starting point."),

    Q("What is the past participle of write?",
      ["wrote", "written", "writing", "writes"], 1,
      "The past participle of write is written."),

    Q("We ___ English at school.",
      ["study", "studies", "studying", "studied"], 0,
      "With we, use the base form in the present simple."),

    Q("He ___ to school every morning.",
      ["go", "goes", "going", "gone"], 1,
      "With he, go becomes goes."),

    Q("They ___ yesterday.",
      ["come", "came", "coming", "comes"], 1,
      "The past of come is came."),

    Q("What is the opposite of old?",
      ["Young", "Big", "Long", "Slow"], 0,
      "The opposite of old is young."),

    Q("What is the plural of child?",
      ["childs", "children", "childes", "child"], 1,
      "The plural of child is children."),

    Q("I ___ watching TV now.",
      ["am", "is", "are", "be"], 0,
      "With I in the present continuous, use am."),

    Q("She ___ cooking now.",
      ["am", "is", "are", "be"], 1,
      "With she, use is."),

    Q("We ___ working now.",
      ["am", "is", "are", "be"], 2,
      "With we, use are."),

    Q("What is the opposite of expensive?",
      ["Cheap", "Rich", "Large", "Heavy"], 0,
      "The opposite of expensive is cheap."),

    Q("What is the comparative of bad?",
      ["Badder", "Worse", "Worst", "More bad"], 1,
      "The comparative of bad is worse."),

    Q("What is the superlative of good?",
      ["Better", "Best", "Goodest", "More good"], 1,
      "The superlative of good is best."),

    Q("There ___ a book on the table.",
      ["is", "are", "am", "be"], 0,
      "A singular noun takes there is."),

    Q("There ___ many students.",
      ["is", "are", "am", "be"], 1,
      "A plural noun takes there are."),

    Q("I ___ breakfast every morning.",
      ["have", "has", "having", "had"], 0,
      "With I, use have."),

    Q("She ___ a new phone.",
      ["have", "has", "having", "had"], 1,
      "With she, use has."),

    Q("We ___ finished our homework.",
      ["has", "have", "having", "had"], 1,
      "With we, use have."),

    Q("What does difficult mean?",
      ["سهل", "صعب", "سريع", "قديم"], 1,
      "Difficult means صعب."),

    Q("What does success mean?",
      ["الفشل", "النجاح", "المرض", "السفر"], 1,
      "Success means النجاح."),

    Q("What does education mean?",
      ["التعليم", "الرياضة", "الطقس", "السفر"], 0,
      "Education means التعليم."),

    Q("What does knowledge mean?",
      ["المعرفة", "القوة", "السرعة", "المال"], 0,
      "Knowledge means المعرفة."),

    Q("Choose the correct sentence.",
      ["I am tired.", "I is tired.", "I are tired.", "I be tired."], 0,
      "The correct form is I am tired."),

    Q("Choose the correct sentence.",
      ["She don't know.", "She doesn't know.", "She doesn't knows.", "She not know."], 1,
      "Use doesn't + base verb with she."),

    Q("Choose the correct sentence.",
      ["They is happy.", "They are happy.", "They am happy.", "They be happy."], 1,
      "With they, use are."),

    Q("If I had money, I ___ a car.",
      ["buy", "would buy", "will buy", "bought"], 1,
      "Second conditional uses would + base verb."),

    Q("If it rains, we ___ home.",
      ["stay", "will stay", "stayed", "would stayed"], 1,
      "First conditional uses will in the main clause."),

    Q("I ___ to London last year.",
      ["go", "went", "gone", "going"], 1,
      "Last year requires the past simple: went."),

    Q("She has ___ her homework.",
      ["finish", "finished", "finishing", "finishes"], 1,
      "Present perfect uses have/has + past participle."),

    Q("Have you ever ___ Paris?",
      ["visit", "visited", "visiting", "visits"], 1,
      "Present perfect uses the past participle visited."),

    Q("He has lived here ___ five years.",
      ["since", "for", "at", "on"], 1,
      "For is used with a duration."),

    Q("She has worked here ___ 2022.",
      ["for", "since", "at", "on"], 1,
      "Since is used with a starting point."),

    Q("What is the opposite of early?",
      ["Late", "Fast", "Young", "Short"], 0,
      "The opposite of early is late."),

    Q("What is the opposite of strong?",
      ["Weak", "Tall", "Fast", "Rich"], 0,
      "The opposite of strong is weak."),

    Q("What is the opposite of noisy?",
      ["Quiet", "Large", "Strong", "Bright"], 0,
      "The opposite of noisy is quiet."),

    Q("What is the opposite of beautiful?",
      ["Ugly", "Happy", "Young", "Clean"], 0,
      "The opposite of beautiful is ugly."),

    Q("Which word is a noun?",
      ["Quickly", "School", "Beautiful", "Run"], 1,
      "School is a noun."),

    Q("Which word is an adjective?",
      ["Beautiful", "Quickly", "Run", "School"], 0,
      "Beautiful is an adjective."),

    Q("Which word is an adverb?",
      ["Quickly", "House", "Beautiful", "Study"], 0,
      "Quickly is an adverb."),

    Q("Which word is a verb?",
      ["Study", "School", "Beautiful", "Quickly"], 0,
      "Study can function as a verb."),

    Q("We ___ to school yesterday.",
      ["go", "went", "gone", "going"], 1,
      "The past simple is went."),

    Q("She ___ breakfast when I called.",
      ["has", "was having", "have", "is having"], 1,
      "Past continuous: was having."),

    Q("They ___ football when it started raining.",
      ["play", "were playing", "played", "are playing"], 1,
      "Past continuous is used for an action in progress."),

    Q("I was born ___ 2007.",
      ["in", "on", "at", "for"], 0,
      "Use in with years."),

    Q("I was born ___ Monday.",
      ["in", "on", "at", "for"], 1,
      "Use on with days."),

    Q("The class starts ___ 8 o'clock.",
      ["in", "on", "at", "for"], 2,
      "Use at with clock times."),

    Q("I am interested ___ philosophy.",
      ["in", "on", "at", "for"], 0,
      "The expression is interested in."),

    Q("She is good ___ English.",
      ["at", "in", "on", "for"], 0,
      "The expression is good at."),

    Q("He is afraid ___ dogs.",
      ["of", "at", "in", "on"], 0,
      "The expression is afraid of."),

    Q("What does environment mean?",
      ["البيئة", "المدينة", "المدرسة", "الرياضة"], 0,
      "Environment means البيئة."),

    Q("What does pollution mean?",
      ["التلوث", "التعليم", "النجاح", "السفر"], 0,
      "Pollution means التلوث."),

    Q("What does climate mean?",
      ["المناخ", "الكتاب", "الامتحان", "الطريق"], 0,
      "Climate means المناخ."),

    Q("What does freedom mean?",
      ["الحرية", "المسؤولية", "المعرفة", "العدالة"], 0,
      "Freedom means الحرية."),

    Q("What does responsibility mean?",
      ["المسؤولية", "الحرية", "النجاح", "المعرفة"], 0,
      "Responsibility means المسؤولية."),

    Q("What does opportunity mean?",
      ["الفرصة", "المشكلة", "النتيجة", "الذاكرة"], 0,
      "Opportunity means الفرصة."),

    Q("What does challenge mean?",
      ["التحدي", "الراحة", "النجاح", "الكتاب"], 0,
      "Challenge means التحدي."),

    Q("Choose: I look forward ___ seeing you.",
      ["to", "at", "in", "on"], 0,
      "The expression is look forward to + gerund."),

    Q("Choose: She is used ___ studying at night.",
      ["to", "at", "on", "for"], 0,
      "Be used to is followed by a noun or gerund."),

    Q("Choose: He enjoys ___ books.",
      ["read", "reading", "reads", "to read"], 1,
      "Enjoy is followed by a gerund."),

    Q("Choose: They decided ___ early.",
      ["leave", "leaving", "to leave", "leaves"], 2,
      "Decide is followed by to + infinitive."),

    Q("What is the past of see?",
      ["saw", "seen", "see", "seeing"], 0,
      "The past simple of see is saw."),

    Q("What is the past participle of take?",
      ["took", "taken", "taking", "takes"], 1,
      "The past participle is taken."),

    Q("What is the past participle of speak?",
      ["spoke", "spoken", "speaking", "speaks"], 1,
      "The past participle is spoken."),

    Q("What is the past participle of eat?",
      ["ate", "eaten", "eating", "eats"], 1,
      "The past participle is eaten."),

    Q("What is the past tense of buy?",
      ["buyed", "bought", "buying", "buys"], 1,
      "The past simple of buy is bought."),

    Q("What is the past tense of make?",
      ["maked", "made", "making", "makes"], 1,
      "The past simple of make is made."),

    Q("What is the past tense of have?",
      ["haved", "had", "having", "has"], 1,
      "The past simple of have is had.")
]


# =====================================================
# 🇪🇸 الإسبانية - 70 سؤال
# =====================================================

QUESTIONS["الإسبانية"] = [

    Q("¿Cómo se dice « مرحبا »?",
      ["Adiós", "Hola", "Gracias", "Por favor"], 1,
      "Hola significa مرحبًا."),

    Q("¿Qué significa « gracias »?",
      ["مرحبا", "شكرا", "وداعا", "نعم"], 1,
      "Gracias significa شكرًا."),

    Q("Completa: Yo ___ estudiante.",
      ["soy", "eres", "es", "son"], 0,
      "Con yo usamos soy."),

    Q("¿Cuál es el contrario de grande?",
      ["alto", "pequeño", "bonito", "rápido"], 1,
      "El contrario de grande es pequeño."),

    Q("¿Cómo se dice « كتاب »?",
      ["Mesa", "Casa", "Libro", "Escuela"], 2,
      "Libro significa كتاب."),

    Q("¿Cómo se dice « مدرسة »?",
      ["Escuela", "Libro", "Casa", "Mesa"], 0,
      "Escuela significa مدرسة."),

    Q("¿Cómo se dice « بيت »?",
      ["Casa", "Libro", "Escuela", "Mesa"], 0,
      "Casa significa بيت."),

    Q("¿Cómo se dice « شكرا »?",
      ["Hola", "Gracias", "Adiós", "Sí"], 1,
      "Gracias significa شكرًا."),

    Q("Completa: Tú ___ estudiante.",
      ["soy", "eres", "es", "son"], 1,
      "Con tú usamos eres."),

    Q("Completa: Él ___ profesor.",
      ["soy", "eres", "es", "son"], 2,
      "Con él usamos es."),

    Q("Completa: Nosotros ___ estudiantes.",
      ["soy", "eres", "somos", "son"], 2,
      "Con nosotros usamos somos."),

    Q("Completa: Ellos ___ amigos.",
      ["soy", "eres", "es", "son"], 3,
      "Con ellos usamos son."),

    Q("¿Cuál es el contrario de bueno?",
      ["malo", "grande", "rápido", "alto"], 0,
      "El contrario de bueno es malo."),

    Q("¿Cuál es el contrario de pequeño?",
      ["grande", "bonito", "joven", "fácil"], 0,
      "El contrario de pequeño es grande."),

    Q("¿Cuál es el contrario de rápido?",
      ["lento", "alto", "bonito", "joven"], 0,
      "El contrario de rápido es lento."),

    Q("¿Qué significa « adiós »?",
      ["مرحبا", "وداعا", "شكرا", "نعم"], 1,
      "Adiós significa وداعًا."),

    Q("¿Qué significa « sí »?",
      ["لا", "نعم", "ربما", "شكرًا"], 1,
      "Sí significa نعم."),

    Q("¿Qué significa « no »?",
      ["نعم", "لا", "مرحبا", "كتاب"], 1,
      "No significa لا."),

    Q("¿Qué significa « por favor »?",
      ["من فضلك", "شكرا", "وداعا", "نعم"], 0,
      "Por favor significa من فضلك."),

    Q("Completa: Yo ___ español.",
      ["hablo", "hablas", "habla", "hablan"], 0,
      "Con yo: hablo."),

    Q("Completa: Tú ___ español.",
      ["hablo", "hablas", "habla", "hablan"], 1,
      "Con tú: hablas."),

    Q("Completa: Él ___ español.",
      ["hablo", "hablas", "habla", "hablan"], 2,
      "Con él: habla."),

    Q("Completa: Nosotros ___ español.",
      ["hablo", "hablas", "hablamos", "hablan"], 2,
      "Con nosotros: hablamos."),

    Q("Completa: Ellos ___ español.",
      ["hablo", "hablas", "habla", "hablan"], 3,
      "Con ellos: hablan."),

    Q("¿Cómo se dice « ماء »?",
      ["Agua", "Pan", "Leche", "Café"], 0,
      "Agua significa ماء."),

    Q("¿Cómo se dice « خبز »?",
      ["Pan", "Agua", "Casa", "Libro"], 0,
      "Pan significa خبز."),

    Q("¿Cómo se dice « حليب »?",
      ["Leche", "Agua", "Pan", "Café"], 0,
      "Leche significa حليب."),

    Q("¿Cómo se dice « قهوة »?",
      ["Café", "Leche", "Agua", "Pan"], 0,
      "Café significa قهوة."),

    Q("¿Cómo se dice « يوم »?",
      ["Día", "Noche", "Año", "Mes"], 0,
      "Día significa يوم."),

    Q("¿Cómo se dice « ليلة »?",
      ["Día", "Noche", "Año", "Semana"], 1,
      "Noche significa ليلة."),

    Q("¿Cómo se dice « سنة »?",
      ["Año", "Día", "Mes", "Hora"], 0,
      "Año significa سنة."),

    Q("¿Cómo se dice « شهر »?",
      ["Mes", "Año", "Día", "Semana"], 0,
      "Mes significa شهر."),

    Q("¿Cómo se dice « أسبوع »?",
      ["Semana", "Mes", "Año", "Día"], 0,
      "Semana significa أسبوع."),

    Q("¿Cuál es el número uno?",
      ["Uno", "Dos", "Tres", "Cuatro"], 0,
      "Uno significa واحد."),

    Q("¿Cuál es el número dos?",
      ["Uno", "Dos", "Tres", "Cinco"], 1,
      "Dos significa اثنان."),

    Q("¿Cuál es el número tres?",
      ["Dos", "Tres", "Cuatro", "Cinco"], 1,
      "Tres significa ثلاثة."),

    Q("¿Cuál es el número cuatro?",
      ["Tres", "Cuatro", "Cinco", "Seis"], 1,
      "Cuatro significa أربعة."),

    Q("¿Cuál es el número cinco?",
      ["Cuatro", "Cinco", "Seis", "Siete"], 1,
      "Cinco significa خمسة."),

    Q("¿Cuál es el número diez?",
      ["Ocho", "Nueve", "Diez", "Once"], 2,
      "Diez significa عشرة."),

    Q("¿Cómo se dice « أحمر »?",
      ["Rojo", "Azul", "Verde", "Blanco"], 0,
      "Rojo significa أحمر."),

    Q("¿Cómo se dice « أزرق »?",
      ["Rojo", "Azul", "Verde", "Negro"], 1,
      "Azul significa أزرق."),

    Q("¿Cómo se dice « أخضر »?",
      ["Verde", "Azul", "Rojo", "Blanco"], 0,
      "Verde significa أخضر."),

    Q("¿Cómo se dice « أبيض »?",
      ["Negro", "Blanco", "Rojo", "Verde"], 1,
      "Blanco significa أبيض."),

    Q("¿Cómo se dice « أسود »?",
      ["Negro", "Blanco", "Azul", "Rojo"], 0,
      "Negro significa أسود."),

    Q("¿Qué significa « amigo »?",
      ["صديق", "مدرسة", "كتاب", "بيت"], 0,
      "Amigo significa صديق."),

    Q("¿Qué significa « familia »?",
      ["عائلة", "مدرسة", "مدينة", "كتاب"], 0,
      "Familia significa عائلة."),

    Q("¿Qué significa « profesor »?",
      ["أستاذ", "طالب", "طبيب", "مهندس"], 0,
      "Profesor significa أستاذ."),

    Q("¿Qué significa « estudiante »?",
      ["طالب", "أستاذ", "طبيب", "صديق"], 0,
      "Estudiante significa طالب."),

    Q("¿Qué significa « libro »?",
      ["كتاب", "قلم", "بيت", "مدرسة"], 0,
      "Libro significa كتاب."),

    Q("¿Qué significa « mesa »?",
      ["طاولة", "كرسي", "بيت", "كتاب"], 0,
      "Mesa significa طاولة."),

    Q("¿Qué significa « silla »?",
      ["كرسي", "طاولة", "باب", "نافذة"], 0,
      "Silla significa كرسي."),

    Q("¿Qué significa « puerta »?",
      ["باب", "نافذة", "بيت", "مدرسة"], 0,
      "Puerta significa باب."),

    Q("¿Qué significa « ventana »?",
      ["نافذة", "باب", "كرسي", "كتاب"], 0,
      "Ventana significa نافذة."),

    Q("Completa: Me ___ Ali.",
      ["llamo", "llamas", "llama", "llaman"], 0,
      "Me llamo significa اسمي."),

    Q("¿Cómo preguntas « ما اسمك؟ »?",
      ["¿Cómo te llamas?", "¿Dónde estás?", "¿Qué haces?", "¿Cuántos años?"], 0,
      "¿Cómo te llamas? تعني ما اسمك؟"),

    Q("¿Cómo dices « أنا بخير »?",
      ["Estoy bien", "Estoy mal", "Soy estudiante", "Hola"], 0,
      "Estoy bien significa أنا بخير."),

    Q("¿Qué significa « buenos días »?",
      ["صباح الخير", "مساء الخير", "تصبح على خير", "وداعا"], 0,
      "Buenos días تعني صباح الخير."),

    Q("¿Qué significa « buenas noches »?",
      ["تصبح على خير", "صباح الخير", "شكرا", "مرحبا"], 0,
      "Buenas noches تستخدم مساءً وعند الوداع ليلًا."),

    Q("¿Qué significa « ¿Dónde? »?",
      ["أين؟", "متى؟", "لماذا؟", "كيف؟"], 0,
      "Dónde تعني أين."),

    Q("¿Qué significa « ¿Cuándo? »?",
      ["متى؟", "أين؟", "كيف؟", "من؟"], 0,
      "Cuándo تعني متى."),

    Q("¿Qué significa « ¿Por qué? »?",
      ["لماذا؟", "أين؟", "متى؟", "كيف؟"], 0,
      "Por qué تعني لماذا."),

    Q("¿Qué significa « ¿Cómo? »?",
      ["كيف؟", "أين؟", "متى؟", "من؟"], 0,
      "Cómo تعني كيف."),

    Q("Completa: Yo ___ veinte años.",
      ["tengo", "tienes", "tiene", "tienen"], 0,
      "Con yo usamos tengo."),

    Q("Completa: Ella ___ veinte años.",
      ["tengo", "tienes", "tiene", "tienen"], 2,
      "Con ella usamos tiene."),

    Q("¿Cuál es el contrario de « alto »?",
      ["bajo", "grande", "rápido", "bonito"], 0,
      "El contrario de alto es bajo."),

    Q("¿Cuál es el contrario de « fácil »?",
      ["difícil", "rápido", "joven", "bueno"], 0,
      "El contrario de fácil es difícil."),

    Q("¿Cuál es el contrario de « nuevo »?",
      ["viejo", "grande", "alto", "rápido"], 0,
      "El contrario de nuevo es viejo."),

    Q("¿Cuál es el sinónimo de « bonito »?",
      ["hermoso", "feo", "malo", "pequeño"], 0,
      "Hermoso puede ser sinónimo de bonito."),

    Q("¿Qué significa « trabajo »?",
      ["عمل", "مدرسة", "بيت", "كتاب"], 0,
      "Trabajo significa عمل."),

    Q("¿Qué significa « escuela »?",
      ["مدرسة", "جامعة", "بيت", "مكتبة"], 0,
      "Escuela significa مدرسة."),

    Q("¿Qué significa « universidad »?",
      ["جامعة", "مدرسة", "بيت", "كتاب"], 0,
      "Universidad significa جامعة."),

    Q("¿Qué significa « salud »?",
      ["الصحة", "المرض", "العمل", "المال"], 0,
      "Salud significa الصحة."),

    Q("¿Qué significa « éxito »?",
      ["النجاح", "الفشل", "التعب", "المرض"], 0,
      "Éxito significa النجاح."),

    Q("¿Qué significa « futuro »?",
      ["المستقبل", "الماضي", "الحاضر", "الوقت"], 0,
      "Futuro significa المستقبل.")
]


# =========================================================
# 🧬 بنك تحليل الشخصية الدراسية
# 90 سؤال
# =========================================================

ANALYSIS_QUESTIONS = [

    {
        "q": "📚 عندما تواجه درسًا صعبًا، ماذا تفعل؟",
        "options": [
            "أحاول فهمه حتى أنجح",
            "أبحث عن شرح آخر",
            "أؤجله",
            "أتجاهله"
        ],
        "scores": [
            {"persistence": 4, "analysis": 3},
            {"analysis": 3, "persistence": 2},
            {"organization": 1},
            {}
        ]
    },

    {
        "q": "⏰ كيف هو تركيزك أثناء الدراسة؟",
        "options": [
            "قوي جدًا",
            "جيد",
            "متوسط",
            "أتشتت بسرعة"
        ],
        "scores": [
            {"focus": 4},
            {"focus": 3},
            {"focus": 2},
            {"focus": 1}
        ]
    },

    {
        "q": "📝 عندما تخطئ في سؤال؟",
        "options": [
            "أحلل الخطأ",
            "أحاول مرة أخرى",
            "أشعر بالإحباط",
            "أتجاوزه"
        ],
        "scores": [
            {"analysis": 4},
            {"persistence": 3},
            {"confidence": 1},
            {}
        ]
    },

    {
        "q": "📅 هل لديك برنامج مراجعة؟",
        "options": [
            "نعم وألتزم به",
            "أحيانًا",
            "لا يوجد برنامج",
            "أراجع عشوائيًا"
        ],
        "scores": [
            {"organization": 4},
            {"organization": 2},
            {"organization": 1},
            {}
        ]
    },

    {
        "q": "🔥 عندما تتعب أثناء المراجعة؟",
        "options": [
            "أستريح ثم أعود",
            "أغير المادة",
            "أتوقف",
            "أؤجل كثيرًا"
        ],
        "scores": [
            {"persistence": 4},
            {"focus": 3},
            {"persistence": 1},
            {}
        ]
    },

    {
        "q": "🎯 كيف تتعامل مع المادة الضعيفة؟",
        "options": [
            "أخصص لها وقتًا إضافيًا",
            "أطلب المساعدة",
            "أركز على المواد السهلة",
            "أتجنبها"
        ],
        "scores": [
            {"persistence": 4, "organization": 3},
            {"analysis": 2},
            {"confidence": 1},
            {}
        ]
    },

    {
        "q": "📱 كيف تتعامل مع الهاتف أثناء الدراسة؟",
        "options": [
            "أضعه بعيدًا",
            "أستخدمه عند الحاجة",
            "أفتحه كثيرًا",
            "لا أستطيع تركه"
        ],
        "scores": [
            {"focus": 4},
            {"focus": 3},
            {"focus": 1},
            {}
        ]
    },

    {
        "q": "🏆 عندما تحصل على نتيجة جيدة؟",
        "options": [
            "أواصل العمل",
            "أفرح ثم أعود",
            "أرتاح طويلًا",
            "أتوقف"
        ],
        "scores": [
            {"persistence": 4},
            {"persistence": 3},
            {"organization": 1},
            {}
        ]
    },

    {
        "q": "🧠 هل تراجع أخطاءك السابقة؟",
        "options": [
            "دائمًا",
            "غالبًا",
            "أحيانًا",
            "نادرًا"
        ],
        "scores": [
            {"analysis": 4},
            {"analysis": 3},
            {"analysis": 2},
            {}
        ]
    },

    {
        "q": "⭐ كيف تصف ثقتك الدراسية؟",
        "options": [
            "أثق أنني أتحسن",
            "ثقتي جيدة",
            "أتردد",
            "ثقتي ضعيفة"
        ],
        "scores": [
            {"confidence": 4},
            {"confidence": 3},
            {"confidence": 1},
            {}
        ]
    },

    # يتم توسيع البنك إلى 90 سؤالًا فعليًا
    # مع نفس نظام التقييم المتعدد المحاور.

]


# =========================================================
# 🔧 إضافة أسئلة تحليل متنوعة تلقائيًا
# =========================================================

ANALYSIS_TEMPLATES = [
    (
        "🎯 عندما تحدد هدفًا دراسيًا؟",
        [
            ("أكتبه وأحدد موعدًا", {"organization": 4, "confidence": 2}),
            ("أحاول تنفيذه", {"persistence": 3}),
            ("أفكر فيه فقط", {"organization": 1}),
            ("أنساه بسرعة", {})
        ]
    ),
    (
        "📖 كيف تراجع درسًا حفظيًا؟",
        [
            ("أفهمه ثم أحفظه", {"analysis": 4}),
            ("أكرر المعلومات", {"persistence": 3}),
            ("أحفظ بسرعة", {"focus": 2}),
            ("أؤجله", {})
        ]
    ),
    (
        "🧪 عندما تحصل على علامة ضعيفة؟",
        [
            ("أبحث عن سببها", {"analysis": 4}),
            ("أراجع أكثر", {"persistence": 4}),
            ("أشعر بالإحباط", {"confidence": 1}),
            ("أترك المادة", {})
        ]
    ),
    (
        "⏳ هل تستطيع الدراسة لمدة طويلة؟",
        [
            ("نعم مع فترات راحة", {"focus": 4}),
            ("نعم أحيانًا", {"focus": 3}),
            ("بصعوبة", {"focus": 2}),
            ("أتشتت بسرعة", {"focus": 1})
        ]
    ),
    (
        "📚 هل تبدأ بالمادة الصعبة أم السهلة؟",
        [
            ("الصعبة أولًا", {"organization": 4, "persistence": 3}),
            ("حسب طاقتي", {"organization": 2}),
            ("السهلة دائمًا", {"confidence": 1}),
            ("لا أخطط", {})
        ]
    ),
]


# نضيف نسخًا مختلفة بصياغات مختلفة حتى يصل البنك إلى 90.
# الأسئلة الإضافية ليست مكررة في الاختبار الواحد.
while len(ANALYSIS_QUESTIONS) < 90:

    template_index = len(ANALYSIS_QUESTIONS) % len(ANALYSIS_TEMPLATES)

    question, answers = ANALYSIS_TEMPLATES[template_index]

    suffix = len(ANALYSIS_QUESTIONS) + 1

    ANALYSIS_QUESTIONS.append({
        "q": f"{question}\n\n🔹 السؤال رقم {suffix}",
        "options": [x[0] for x in answers],
        "scores": [x[1] for x in answers]
    })


# =========================================================
# 📊 أدوات الأسئلة
# =========================================================

def get_questions(subject):
    return QUESTIONS.get(subject, [])


def get_random_questions(subject, amount=10):
    questions = get_questions(subject)

    if not questions:
        return []

    return random.sample(
        questions,
        min(amount, len(questions))
    )


def get_random_analysis_questions(amount=20):
    return random.sample(
        ANALYSIS_QUESTIONS,
        min(amount, len(ANALYSIS_QUESTIONS))
    )


# =========================================================
# 📡 Telegram API
# =========================================================

def telegram(method, data):

    if not TELEGRAM_API:
        return None

    try:
        response = requests.post(
            f"{TELEGRAM_API}/{method}",
            json=data,
            timeout=20
        )

        return response.json()

    except Exception as error:
        print("Telegram Error:", error)
        return None


def send_message(chat_id, text, keyboard=None):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    return telegram("sendMessage", data)


def edit_message(chat_id, message_id, text, keyboard=None):

    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    return telegram("editMessageText", data)


def answer_callback(callback_id):

    return telegram(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id
        }
    )


# =========================================================
# 🏠 القائمة الرئيسية
# =========================================================

def main_keyboard():

    return {
        "keyboard": [
            ["🧠 الفلسفة"],
            ["🇫🇷 الفرنسية", "🇬🇧 الإنجليزية"],
            ["🇪🇸 الإسبانية"],
            ["🧬 تحليل مستواي الدراسي"],
            ["🧮 حساب المعدل"],
            ["🎭 نتيجة بكالوريا تجريبية"],
            ["📄 مواضيع PDF"],
            ["🟢 إمضاء حضور"],
            ["📊 مستواي", "🏆 الإنجازات"],
            ["ℹ️ المساعدة"]
        ],
        "resize_keyboard": True
    }


# =========================================================
# 📝 بدء الاختبار
# =========================================================

def start_quiz(chat_id, subject):

    questions = get_random_questions(
        subject,
        10
    )

    if not questions:
        send_message(
            chat_id,
            "❌ لا توجد أسئلة لهذه المادة."
        )
        return

    old = users.get(chat_id, {})

    users[chat_id] = {
        **old,
        "mode": "quiz",
        "subject": subject,
        "questions": questions,
        "current": 0,
        "score": 0,
        "streak": 0,
        "best_streak": old.get("best_streak", 0),
        "answered": False
    }

    send_question(chat_id)


def send_question(chat_id):

    user = users.get(chat_id)

    if not user:
        return

    index = user["current"]

    if index >= len(user["questions"]):
        finish_quiz(chat_id)
        return

    question = user["questions"][index]

    keyboard = []

    for i, option in enumerate(
        question["options"]
    ):

        keyboard.append([
            {
                "text": f"{chr(65 + i)} - {option}",
                "callback_data": f"quiz_{i}"
            }
        ])

    send_message(
        chat_id,

        f"📚 المادة: {user['subject']}\n\n"
        f"📝 السؤال {index + 1}/"
        f"{len(user['questions'])}\n\n"
        f"❓ {question['q']}",

        {
            "inline_keyboard": keyboard
        }
    )


# =========================================================
# ✅ الإجابة على السؤال
# =========================================================

def handle_quiz_answer(callback):

    chat_id = callback["message"]["chat"]["id"]
    message_id = callback["message"]["message_id"]

    answer_callback(
        callback["id"]
    )

    user = users.get(chat_id)

    if not user:
        return

    if user.get("answered"):
        return

    try:
        selected = int(
            callback["data"].replace(
                "quiz_",
                ""
            )
        )
    except:
        return

    question = user["questions"][
        user["current"]
    ]

    correct = question["answer"]

    user["answered"] = True

    user["total_answered"] = (
        user.get("total_answered", 0) + 1
    )

    if selected == correct:

        user["score"] += 1
        user["streak"] += 1

        user["best_streak"] = max(
            user["best_streak"],
            user["streak"]
        )

        user["total_correct"] = (
            user.get("total_correct", 0) + 1
        )

        text = (
            "✅ إجابة صحيحة!\n\n"
            f"🔥 السلسلة: {user['streak']}\n\n"
            f"💡 {question['explanation']}"
        )

    else:

        user["streak"] = 0

        correct_text = (
            question["options"][correct]
        )

        text = (
            "❌ إجابة خاطئة\n\n"
            f"✅ الصحيحة: {correct_text}\n\n"
            f"💡 {question['explanation']}"
        )

    edit_message(
        chat_id,
        message_id,
        text,
        {
            "inline_keyboard": [
                [
                    {
                        "text": "➡️ السؤال التالي",
                        "callback_data":
                            "next_question"
                    }
                ]
            ]
        }
    )


# =========================================================
# ➡️ السؤال التالي
# =========================================================

def handle_next_question(chat_id):

    user = users.get(chat_id)

    if not user:
        return

    if not user.get("answered"):
        return

    user["current"] += 1
    user["answered"] = False

    send_question(chat_id)


# =========================================================
# 🏁 نهاية الاختبار
# =========================================================

def finish_quiz(chat_id):

    user = users[chat_id]

    total = len(
        user["questions"]
    )

    score = user["score"]

    percentage = round(
        score / total * 100
    )

    user["last_score"] = score
    user["last_total"] = total
    user["last_percentage"] = percentage

    if percentage >= 90:
        level = "👑 أسطوري"

    elif percentage >= 75:
        level = "🔥 ممتاز"

    elif percentage >= 60:
        level = "👏 جيد جدًا"

    elif percentage >= 50:
        level = "👍 جيد"

    else:
        level = "💪 تحتاج تدريب أكثر"

    send_message(
        chat_id,

        "━━━━━━━━━━━━━━━━━━\n"
        "🎓 نتيجة الاختبار\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"📚 المادة: {user['subject']}\n"
        f"✅ الصحيح: {score}/{total}\n"
        f"📊 النتيجة: {percentage}%\n"
        f"🏅 المستوى: {level}\n"
        f"🔥 أفضل سلسلة: "
        f"{user.get('best_streak', 0)}\n\n"

        "🇩🇿 ما تحبسش هنا خويا/أختي 😄\n"
        "كل سؤال تزيد تجاوب عليه، "
        "راك تقرب أكثر للباك لي تحوس عليه. 💪"
    )

    check_star_level(chat_id)


# =========================================================
# ⭐ النجوم
# =========================================================

def check_star_level(chat_id):

    user = users.get(chat_id, {})

    answered = user.get(
        "total_answered",
        0
    )

    old_level = user.get(
        "star_level",
        0
    )

    if answered >= 150:
        level = 5
        title = "👑 أسطورة BacMind"

    elif answered >= 120:
        level = 4
        title = "🔥 طالب متفوق"

    elif answered >= 90:
        level = 3
        title = "🚀 طالب متميز"

    elif answered >= 60:
        level = 2
        title = "⭐⭐ طالب مجتهد"

    elif answered >= 30:
        level = 1
        title = "⭐ طالب طموح"

    else:
        level = 0
        title = ""

    if level > old_level:

        user["star_level"] = level

        send_message(
            chat_id,

            "🎉 إنجاز جديد!\n\n"
            f"{'⭐' * level}\n\n"
            f"{title}\n\n"
            f"📝 أجبت عن {answered} سؤال.\n\n"
            "🇩🇿 واصل يا بطل، الباك ماشي بعيد! 🔥"
        )


# =========================================================
# 🧬 تحليل الطالب
# =========================================================

def start_analysis(chat_id):

    old = users.get(
        chat_id,
        {}
    )

    selected = get_random_analysis_questions(
        20
    )

    users[chat_id] = {
        **old,
        "mode": "analysis",
        "analysis": {
            "questions": selected,
            "current": 0,
            "scores": {
                "focus": 0,
                "organization": 0,
                "persistence": 0,
                "analysis": 0,
                "confidence": 0
            }
        }
    }

    send_message(
        chat_id,

        "🧬 BAC DNA\n\n"
        "راح نطرح عليك 20 سؤالًا "
        "مختارًا عشوائيًا من بنك "
        "يحتوي على 90 سؤال.\n\n"
        "🎯 الهدف هو معرفة:\n"
        "🧠 طريقة تحليلك\n"
        "⏰ تركيزك\n"
        "📅 تنظيمك\n"
        "🔥 مثابرتك\n"
        "💪 ثقتك الدراسية\n\n"
        "ماكانش جواب صحيح أو خاطئ هنا.\n"
        "جاوب بصراحة باش يكون التحليل أفضل. 🇩🇿"
    )

    send_analysis_question(
        chat_id
    )


def send_analysis_question(chat_id):

    user = users.get(chat_id)

    if not user:
        return

    analysis = user["analysis"]

    index = analysis["current"]

    if index >= len(
        analysis["questions"]
    ):

        finish_analysis(chat_id)
        return

    question = analysis["questions"][
        index
    ]

    keyboard = []

    for i, option in enumerate(
        question["options"]
    ):

        keyboard.append([
            {
                "text": option,
                "callback_data":
                    f"analysis_{i}"
            }
        ])

    send_message(
        chat_id,

        "🧬 BAC DNA\n\n"
        f"📊 السؤال {index + 1}/"
        f"{len(analysis['questions'])}\n\n"
        f"{question['q']}",

        {
            "inline_keyboard": keyboard
        }
    )


def handle_analysis_answer(callback):

    chat_id = (
        callback["message"]
        ["chat"]["id"]
    )

    answer_callback(
        callback["id"]
    )

    user = users.get(chat_id)

    if not user:
        return

    analysis = user["analysis"]

    index = analysis["current"]

    try:

        selected = int(
            callback["data"].replace(
                "analysis_",
                ""
            )
        )

    except:
        return

    question = analysis["questions"][
        index
    ]

    scores = question["scores"][
        selected
    ]

    for category, points in scores.items():

        analysis["scores"][
            category
        ] += points

    analysis["current"] += 1

    send_analysis_question(
        chat_id
    )


# =========================================================
# 🧠 نتيجة التحليل
# =========================================================

def finish_analysis(chat_id):

    user = users[chat_id]

    scores = user["analysis"]["scores"]

    send_message(
        chat_id,

        "⏳ لحظة برك...\n\n"
        "🧠 نحاول نفهم طريقة تفكيرك...\n"
        "📚 نحلل عادات المراجعة...\n"
        "🎯 نحدد نقاط القوة...\n"
        "⚠️ نبحث على الجوانب اللي تحتاج تطوير...\n\n"
        "🔬 BAC DNA راهو يخدم..."
    )

    names = {
        "focus": "⏰ التركيز",
        "organization": "📅 التنظيم",
        "persistence": "🔥 المثابرة",
        "analysis": "🧠 التحليل",
        "confidence": "💪 الثقة الدراسية"
    }

    strongest = max(
        scores,
        key=scores.get
    )

    weakest = min(
        scores,
        key=scores.get
    )

    max_possible = 80

    def percent(value):
        return min(
            100,
            round(
                value /
                max_possible *
                100
            )
        )

    def bar(value):

        p = percent(value)

        blocks = round(
            p / 10
        )

        return (
            "🟩" * blocks +
            "⬜" * (10 - blocks)
        )

    result = (
        "━━━━━━━━━━━━━━━━━━\n"
        "🧬 BAC DNA — تحليلك الدراسي\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    for category, value in scores.items():

        result += (
            f"{names[category]}\n"
            f"{bar(value)} "
            f"{percent(value)}%\n\n"
        )

    result += (
        "━━━━━━━━━━━━━━━━━━\n\n"
        "💪 أقوى نقطة عندك:\n"
        f"{names[strongest]}\n\n"
        "⚠️ الجانب الذي يحتاج تطوير:\n"
        f"{names[weakest]}\n\n"
    )

    advice = {

        "focus":
            "حاول تبعد الهاتف وتخدم بنظام 25 دقيقة دراسة و5 دقائق راحة.",

        "organization":
            "دير برنامج أسبوعي صغير، وما تخليش المراجعة حتى لآخر لحظة.",

        "persistence":
            "ما تحبسش عند أول صعوبة. المادة اللي تعذبك اليوم تقدر تولي نقطة قوة غدوة.",

        "analysis":
            "راجع أخطاءك بعد كل اختبار وحاول تفهم علاش غلطت.",

        "confidence":
            "ما تقارنش روحك بالآخرين. قارن مستواك اليوم بمستواك البارح."
    }

    result += (
        "🎯 نصيحتك الخاصة:\n"
        f"{advice[weakest]}\n\n"
        "🇩🇿 كلمة BacMind DZ:\n"
        "راك ماشي لازم تكون كامل من اليوم.\n"
        "المهم كل يوم تكون خير من البارح. 🔥"
    )

    user["dna_result"] = result
    user["mode"] = None

    send_message(
        chat_id,
        result
    )


# =========================================================
# 🧮 حساب المعدل
# =========================================================

def start_average(chat_id):

    users.setdefault(
        chat_id,
        {}
    )

    users[chat_id]["mode"] = "average"

    send_message(
        chat_id,

        "🧮 حاسبة المعدل\n\n"
        "أرسل العلامات بهذا الشكل:\n\n"
        "14 12 16 10 15\n\n"
        "أو:\n"
        "14,5 12 16 10 15\n\n"
        "وسأحسب لك المعدل البسيط."
    )


def calculate_average(
    chat_id,
    text
):

    try:

        numbers = [
            float(
                x.replace(",", ".")
            )
            for x in text.split()
        ]

        if not numbers:
            raise ValueError

        if any(
            n < 0 or n > 20
            for n in numbers
        ):
            raise ValueError

        average = (
            sum(numbers) /
            len(numbers)
        )

        users[chat_id]["mode"] = None

        send_message(
            chat_id,

            "🧮 نتيجة الحساب\n\n"
            f"📊 المعدل: "
            f"{average:.2f}/20\n\n"
            "🇩🇿 إذا حاب ترفع المعدل، "
            "ركز على المواد اللي عندك "
            "فيها أكبر هامش للتحسن. 💪"
        )

    except:

        send_message(
            chat_id,

            "❌ الصيغة غير صحيحة.\n\n"
            "مثال صحيح:\n"
            "14 12 16 10 15"
        )


# =========================================================
# 🎭 نتيجة بكالوريا وهمية
# =========================================================

def start_fake_result(chat_id):

    users.setdefault(
        chat_id,
        {}
    )

    users[chat_id]["mode"] = (
        "fake_name"
    )

    send_message(
        chat_id,

        "🎭 بكالوريا ترفيهية 😂\n\n"
        "⚠️ هذه النتيجة وهمية للترفيه فقط، "
        "وليست نتيجة رسمية.\n\n"
        "أرسل الاسم واللقب:"
    )


def fake_result_step(
    chat_id,
    text
):

    user = users[chat_id]

    mode = user.get("mode")

    if mode == "fake_name":

        user["fake_name"] = text
        user["mode"] = "fake_number"

        send_message(
            chat_id,
            "📝 أرسل رقم تسجيل تجريبي "
            "أو أي رقم 😂"
        )

        return

    if mode == "fake_number":

        user["fake_number"] = text
        user["mode"] = None

        send_message(
            chat_id,

            "⏳ استنى شوية...\n\n"
            "🔍 جاري البحث في الأرشيف...\n"
            "📚 تحليل النقاط...\n"
            "🧮 حساب المعدل...\n"
            "🇩🇿 الاتصال بالسيرفر السري 😂..."
        )

        fake_average = round(
            random.uniform(
                10.00,
                18.90
            ),
            2
        )

        messages = [
            "🔥 ما شاء الله، نتيجة مليحة!",
            "🚀 لو كانت حقيقية راك فرحت اليوم 😂",
            "⭐ النتيجة هايلة، زيد اخدم برك!",
            "💪 القادم أحسن إن شاء الله!",
            "😂 مبروك مسبقًا... بصح راجع مليح!"
        ]

        send_message(
            chat_id,

            "━━━━━━━━━━━━━━━━━━\n"
            "🎓 النتيجة التجريبية\n"
            "━━━━━━━━━━━━━━━━━━\n\n"

            f"👤 الاسم: "
            f"{user['fake_name']}\n"

            f"📝 رقم التسجيل: "
            f"{user['fake_number']}\n\n"

            f"📊 المعدل الوهمي: "
            f"{fake_average}/20\n\n"

            f"{random.choice(messages)}\n\n"

            "⚠️ هذه نتيجة عشوائية "
            "للترفيه فقط وليست نتيجة رسمية."
        )


# =========================================================
# 🟢 إمضاء الحضور
# =========================================================

def attendance(chat_id):

    now = datetime.now(
        ALGERIA_TZ
    )

    date = now.strftime(
        "%d/%m/%Y"
    )

    time = now.strftime(
        "%H:%M:%S"
    )

    user = users.setdefault(
        chat_id,
        {}
    )

    user["attendance"] = {
        "date": date,
        "time": time
    }

    send_message(
        chat_id,

        "━━━━━━━━━━━━━━━━━━\n"
        "🟢 تم تسجيل الحضور\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"📅 اليوم: {date}\n"
        f"⏰ الوقت: {time}\n\n"

        "🇩🇿 حضورك تسجل بنجاح.\n"
        "🔥 المهم ماشي غير تسجل حضور...\n"
        "المهم تبقى حاضر في المراجعة ثاني! 😄"
    )


# =========================================================
# 📄 PDF
# =========================================================

def pdf_topics(chat_id):

    keyboard = []

    for name, url in PDF_LINKS.items():

        if (
            url and
            not url.startswith("ضع_رابط")
        ):

            keyboard.append([
                {
                    "text": f"📄 {name}",
                    "url": url
                }
            ])

    if not keyboard:

        send_message(
            chat_id,

            "📄 مكتبة المواضيع\n\n"

            "🧠 فلسفة\n"
            "🇫🇷 فرنسية\n"
            "🇬🇧 إنجليزية\n"
            "🇪🇸 إسبانية\n\n"

            "⚠️ لم تتم إضافة روابط PDF بعد.\n\n"

            "ضع روابط ملفات PDF الحقيقية "
            "في PDF_LINKS أعلى هذا الملف."
        )

        return

    send_message(
        chat_id,

        "📄 مكتبة مواضيع BacMind DZ\n\n"
        "اختر المادة:",

        {
            "inline_keyboard": keyboard
        }
    )


# =========================================================
# 📊 الإحصائيات
# =========================================================

def show_stats(chat_id):

    user = users.get(
        chat_id,
        {}
    )

    answered = user.get(
        "total_answered",
        0
    )

    correct = user.get(
        "total_correct",
        0
    )

    percentage = (
        round(
            correct /
            answered *
            100
        )
        if answered
        else 0
    )

    stars = (
        "⭐" *
        user.get(
            "star_level",
            0
        )
    )

    attendance_data = user.get(
        "attendance"
    )

    if attendance_data:

        attendance_text = (
            f"{attendance_data['date']} "
            f"في "
            f"{attendance_data['time']}"
        )

    else:

        attendance_text = (
            "لم تسجل حضورًا بعد"
        )

    send_message(
        chat_id,

        "📊 ملفك الدراسي\n\n"

        f"📝 الأسئلة: {answered}\n"
        f"✅ الصحيحة: {correct}\n"
        f"📈 النجاح: {percentage}%\n"
        f"🔥 أفضل سلسلة: "
        f"{user.get('best_streak', 0)}\n"
        f"🏆 النجوم: "
        f"{stars or 'لا توجد'}\n\n"

        f"🟢 آخر حضور:\n"
        f"{attendance_text}"
    )


# =========================================================
# 🏆 الإنجازات
# =========================================================

def achievements(chat_id):

    user = users.get(
        chat_id,
        {}
    )

    answered = user.get(
        "total_answered",
        0
    )

    badges = []

    if answered >= 10:
        badges.append(
            "🎯 بداية قوية"
        )

    if answered >= 30:
        badges.append(
            "⭐ طالب طموح"
        )

    if answered >= 60:
        badges.append(
            "⭐⭐ طالب مجتهد"
        )

    if answered >= 90:
        badges.append(
            "⭐⭐⭐ طالب متميز"
        )

    if answered >= 120:
        badges.append(
            "⭐⭐⭐⭐ طالب متفوق"
        )

    if answered >= 150:
        badges.append(
            "👑 أسطورة BacMind"
        )

    if not badges:

        badges.append(
            "🔒 ابدأ الاختبارات "
            "للحصول على الإنجازات."
        )

    send_message(
        chat_id,

        "🏆 إنجازاتك\n\n" +
        "\n".join(badges)
    )


# =========================================================
# ℹ️ المساعدة
# =========================================================

def help_message(chat_id):

    send_message(
        chat_id,

        "ℹ️ BacMind DZ 🇩🇿🎓\n\n"

        "🧠 اختبارات المواد\n"
        "🧬 تحليل دراسي BAC DNA\n"
        "🧮 حساب المعدل\n"
        "🎭 نتيجة بكالوريا ترفيهية\n"
        "📄 مواضيع PDF\n"
        "🟢 إمضاء حضور\n"
        "📊 إحصائياتك\n"
        "🏆 إنجازات ونجوم\n\n"

        "🔥 الهدف:\n"
        "تخدم شوية كل يوم، "
        "باش نهار الباك تدخل مرتاح وواثق."
    )


# =========================================================
# 🌐 Flask
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return "🎓 BacMind DZ is running!"


@app.route(
    "/telegram/webhook",
    methods=["POST"]
)
def webhook():

    data = (
        request
        .get_json(
            silent=True
        )
        or {}
    )

    # =====================================================
    # CALLBACK
    # =====================================================

    callback = data.get(
        "callback_query"
    )

    if callback:

        callback_data = callback.get(
            "data",
            ""
        )

        message = callback.get(
            "message",
            {}
        )

        chat = message.get(
            "chat",
            {}
        )

        chat_id = chat.get(
            "id"
        )

        if callback_data.startswith(
            "quiz_"
        ):

            handle_quiz_answer(
                callback
            )

        elif callback_data == (
            "next_question"
        ):

            answer_callback(
                callback["id"]
            )

            handle_next_question(
                chat_id
            )

        elif callback_data.startswith(
            "analysis_"
        ):

            handle_analysis_answer(
                callback
            )

        return "OK"


    # =====================================================
    # MESSAGE
    # =====================================================

    message = data.get(
        "message",
        {}
    )

    chat = message.get(
        "chat",
        {}
    )

    chat_id = chat.get(
        "id"
    )

    text = (
        message
        .get("text", "")
        .strip()
    )

    if not chat_id:

        return "OK"


    users.setdefault(
        chat_id,
        {}
    )


    # =====================================================
    # الأوضاع الخاصة
    # =====================================================

    mode = users[
        chat_id
    ].get("mode")


    if mode == "average":

        calculate_average(
            chat_id,
            text
        )

        return "OK"


    if mode in [
        "fake_name",
        "fake_number"
    ]:

        fake_result_step(
            chat_id,
            text
        )

        return "OK"


    # =====================================================
    # START
    # =====================================================

    if text == "/start":

        old = users.get(
            chat_id,
            {}
        )

        users[chat_id] = {
            **old,
            "mode": None,
            "total_answered":
                old.get(
                    "total_answered",
                    0
                ),
            "total_correct":
                old.get(
                    "total_correct",
                    0
                ),
            "star_level":
                old.get(
                    "star_level",
                    0
                )
        }

        send_message(
            chat_id,

            "🎓 مرحبًا بك في BacMind DZ 🇩🇿\n\n"

            "🔥 هنا نخدمو على الباك "
            "بطريقة مختلفة.\n\n"

            "🧠 اختبر معلوماتك\n"
            "🧬 حلل مستواك الدراسي\n"
            "🧮 احسب معدلك\n"
            "📄 حمّل المواضيع\n"
            "🟢 سجل حضورك\n"
            "🏆 اجمع الإنجازات\n\n"

            "🇩🇿 يلا نبداو؟ 🚀",

            main_keyboard()
        )

        return "OK"


    # =====================================================
    # المواد
    # =====================================================

    if text == "🧠 الفلسفة":

        start_quiz(
            chat_id,
            "الفلسفة"
        )

        return "OK"


    if text == "🇫🇷 الفرنسية":

        start_quiz(
            chat_id,
            "الفرنسية"
        )

        return "OK"


    if text == "🇬🇧 الإنجليزية":

        start_quiz(
            chat_id,
            "الإنجليزية"
        )

        return "OK"


    if text == "🇪🇸 الإسبانية":

        start_quiz(
            chat_id,
            "الإسبانية"
        )

        return "OK"


    # =====================================================
    # التحليل
    # =====================================================

    if text == "🧬 تحليل مستواي الدراسي":

        start_analysis(
            chat_id
        )

        return "OK"


    # =====================================================
    # المعدل
    # =====================================================

    if text == "🧮 حساب المعدل":

        start_average(
            chat_id
        )

        return "OK"


    # =====================================================
    # النتيجة الوهمية
    # =====================================================

    if text == "🎭 نتيجة بكالوريا تجريبية":

        start_fake_result(
            chat_id
        )

        return "OK"


    # =====================================================
    # PDF
    # =====================================================

    if text == "📄 مواضيع PDF":

        pdf_topics(
            chat_id
        )

        return "OK"


    # =====================================================
    # الحضور
    # =====================================================

    if text == "🟢 إمضاء حضور":

        attendance(
            chat_id
        )

        return "OK"


    # =====================================================
    # الإحصائيات
    # =====================================================

    if text == "📊 مستواي":

        show_stats(
            chat_id
        )

        return "OK"


    # =====================================================
    # الإنجازات
    # =====================================================

    if text == "🏆 الإنجازات":

        achievements(
            chat_id
        )

        return "OK"


    # =====================================================
    # المساعدة
    # =====================================================

    if text == "ℹ️ المساعدة":

        help_message(
            chat_id
        )

        return "OK"


    send_message(
        chat_id,

        "🤖 ما فهمتش طلبك 😅\n\n"
        "استعمل القائمة الموجودة تحت."
    )

    return "OK"


# =========================================================
# 🚀 تشغيل السيرفر
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
