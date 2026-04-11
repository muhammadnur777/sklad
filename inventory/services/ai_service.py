import json
import logging
from decouple import config
from google import genai
from google.genai import types
from .ai_tools import TOOLS_REGISTRY

logger = logging.getLogger(__name__)

# Gemini клиент
client = genai.Client(api_key=config('GEMINI_API_KEY'))
MODEL = 'gemini-2.5-flash'

# System prompt
SYSTEM_PROMPT = """Sen SKLAD tizimining AI analitik yordamchisisan.
Sening vazifang — foydalanuvchining savollarga javob berish, sotuvlar va ombor haqida tahlil qilish.

Qoidalar:
1. Faqat o'qish (read-only) — hech narsa o'zgartirma
2. Javoblarni qisqa va aniq yoz
3. Raqamlarni formatlangan holda ko'rsat (bo'sh joy bilan: 1 000 000)
4. Xulosalar va tavsiyalar ber
5. MUHIM: Foydalanuvchi qaysi tilda yozsa, SHU tilda javob ber. Tillarni aralashtirib yuborma!
6. Agar savol rus tilida bo'lsa — butun javobni faqat rus tilida yoz
7. Agar savol o'zbek tilida bo'lsa — butun javobni faqat o'zbek tilida yoz
7. Agar ma'lumot topilmasa — ochiq ayt

Mavjud ma'lumotlar:
- Sotuvlar (BazarSale) — bozordagi sotuvlar
- Tovarlar (Product) — ombordagi tovarlar
- Ketuvlar (Sale) — bozorga jo'natishlar
- Qarzdorlar — to'lanmagan sotuvlar
- Narx tarixi — narx o'zgarishlari
- 2 ta do'kon: Aziz 3 89 va Siroj 1 84

Periods: bugun, hafta, oy, yil, oxirgi_30, oxirgi_90, barchasi, YYYY-MM (masalan 2026-04), YYYY-MM-DD (masalan 2026-04-01).
Agar foydalanuvchi "1 aprelda" desa — period='2026-04-01' ishlatilsin.
Agar foydalanuvchi "barcha vaqt", "за все время" desa — period='barchasi' ishlatilsin."""
# Tool declarations для Gemini
TOOL_DECLARATIONS = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name='get_sales_by_product',
            description='Muayyan tovar bo\'yicha sotuvlar ma\'lumotini olish. Qancha sotilgan, qaysi do\'konda, qancha summaga.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'product_name': types.Schema(type=types.Type.STRING, description='Tovar nomi yoki qismi'),
                    'period': types.Schema(type=types.Type.STRING, description='Davr: bugun, hafta, oy, yil, oxirgi_30, oxirgi_90, barchasi, YYYY-MM (masalan 2026-04), yoki YYYY-MM-DD (masalan 2026-04-01)'),
                },
                required=['product_name'],
            ),
        ),
        types.FunctionDeclaration(
            name='get_top_products',
            description='Eng ko\'p sotilgan tovarlar reytingi.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'limit': types.Schema(type=types.Type.INTEGER, description='Nechta tovar ko\'rsatish (default: 10)'),
                    'period': types.Schema(type=types.Type.STRING, description='Davr: bugun, hafta, oy, yil, oxirgi_30, oxirgi_90, barchasi, YYYY-MM (masalan 2026-04), yoki YYYY-MM-DD (masalan 2026-04-01)'),
                    'sort_by': types.Schema(type=types.Type.STRING, description='quantity yoki revenue'),
                },
            ),
        ),
        types.FunctionDeclaration(
            name='get_revenue',
            description='Umumiy tushum (daromad) ma\'lumotlari. To\'langan va qarz bo\'yicha.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'period': types.Schema(type=types.Type.STRING, description='Davr: bugun, hafta, oy, yil, oxirgi_30, oxirgi_90, barchasi, YYYY-MM (masalan 2026-04), yoki YYYY-MM-DD (masalan 2026-04-01)'),
                },
            ),
        ),
        types.FunctionDeclaration(
            name='get_daily_sales',
            description='Kunlik sotuvlar statistikasi. Trendlarni ko\'rish uchun.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'period': types.Schema(type=types.Type.STRING, description='Davr: bugun, hafta, oy, yil, oxirgi_30, oxirgi_90, barchasi, YYYY-MM (masalan 2026-04), yoki YYYY-MM-DD (masalan 2026-04-01)'),
                },
            ),
        ),
        types.FunctionDeclaration(
            name='get_debts_info',
            description='Qarzdorlar haqida ma\'lumot. Kimlar qarz, qancha summa.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
            ),
        ),
        types.FunctionDeclaration(
            name='get_warehouse_info',
            description='Ombor (sklad) haqida ma\'lumot. Umumiy qiymat, kam qolgan tovarlar.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
            ),
        ),
        types.FunctionDeclaration(
            name='get_shipments_info',
            description='Bozorga ketuvlar (jo\'natishlar) haqida ma\'lumot.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'period': types.Schema(type=types.Type.STRING, description='Davr: bugun, hafta, oy, yil, oxirgi_30, oxirgi_90, barchasi, YYYY-MM (masalan 2026-04), yoki YYYY-MM-DD (masalan 2026-04-01)'),
                },
            ),
        ),
        types.FunctionDeclaration(
            name='get_price_changes',
            description='Narx o\'zgarishlari tarixi.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'limit': types.Schema(type=types.Type.INTEGER, description='Nechta o\'zgarish ko\'rsatish'),
                },
            ),
        ),
        types.FunctionDeclaration(
            name='get_comparison',
            description='Ikki davrni solishtirish. Masalan, bu oy vs o\'tgan oy.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'period1': types.Schema(type=types.Type.STRING, description='Birinchi davr: bugun, hafta, oy, yil, oxirgi_30, oxirgi_90, barchasi, YYYY-MM (masalan 2026-03), yoki YYYY-MM-DD'),
                    'period2': types.Schema(type=types.Type.STRING, description='Ikkinchi davr: bugun, hafta, oy, yil, oxirgi_30, oxirgi_90, barchasi, YYYY-MM (masalan 2026-04), yoki YYYY-MM-DD'),
                },
                required=['period1', 'period2'],
            ),
        ),
    ]),
]


def execute_tool(function_name: str, args: dict) -> str:
    """Функцияни xavfsiz bajarish."""
    if function_name not in TOOLS_REGISTRY:
        return json.dumps({'error': f'Noma\'lum funksiya: {function_name}'})

    try:
        func = TOOLS_REGISTRY[function_name]
        result = func(**args)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f'Tool execution error: {function_name}, args={args}, error={e}')
        return json.dumps({'error': f'Xatolik: {str(e)}'})


def chat_with_ai(user_message: str, chat_history: list = None) -> str:
    """
    AI bilan suhbatlashish.
    chat_history: [{'role': 'user', 'text': '...'}, {'role': 'assistant', 'text': '...'}]
    """
    try:
        # Xabarlar tayyorlash
        contents = []

        # Oldingi xabarlar
        if chat_history:
            for msg in chat_history[-10:]:  # Oxirgi 10 ta xabar
                role = 'user' if msg['role'] == 'user' else 'model'
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg['text'])],
                ))

        # Yangi xabar
        contents.append(types.Content(
            role='user',
            parts=[types.Part.from_text(text=user_message)],
        ))

        # Gemini ga so'rov
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=TOOL_DECLARATIONS,
                temperature=0.3,
            ),
        )

        # Function call bormi?
        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Tekshiramiz function call bormi
            has_function_call = False
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        has_function_call = True
                        break

            if not has_function_call:
                break

            # Function call larni bajaramiz
            function_responses = []
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    fc = part.function_call
                    logger.info(f'AI calling: {fc.name}({fc.args})')

                    result = execute_tool(fc.name, dict(fc.args) if fc.args else {})

                    function_responses.append(
                        types.Part.from_function_response(
                            name=fc.name,
                            response={'result': result},
                        )
                    )

            # Natijalarni qaytaramiz
            contents.append(response.candidates[0].content)
            contents.append(types.Content(
                role='user',
                parts=function_responses,
            ))

            # Yangi so'rov
            response = client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=TOOL_DECLARATIONS,
                    temperature=0.3,
                ),
            )

        # Javobni olamiz
        if response.candidates and response.candidates[0].content.parts:
            text_parts = []
            for part in response.candidates[0].content.parts:
                if part.text:
                    text_parts.append(part.text)
            return '\n'.join(text_parts) if text_parts else 'Javob topilmadi.'

        return 'Javob topilmadi.'

    except Exception as e:
        logger.error(f'AI chat error: {e}')
        return f'Xatolik yuz berdi: {str(e)}'