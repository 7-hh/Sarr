import google.generativeai as genai

from config import settings


class AIEngine:
    def __init__(self) -> None:
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.ai_model)

    async def generate_reply(self, persona: str, incoming: str) -> str:
        prompt = (
            f"{persona}\n"
            "اكتب بالعربية الطبيعية المفهومة وذكية حسب سياق الرسالة.\n"
            'ابدأ الرد دائمًا بكلمة "سائر...".\n'
            "أجب إجابة عملية ومباشرة عند الحاجة، بدون غموض زائد.\n"
            "اجعل الرد احترافيًا ومفيدًا للمستخدم.\n"
            f"رسالة الطرف الآخر: {incoming}"
        )
        try:
            response = await self.model.generate_content_async(prompt)
            text = (response.text or "").strip()
            if not text:
                return "سائر... حصل فراغ في الاستجابة. أعد صياغة سؤالك وسأجيبك أدق."
            if not text.startswith("سائر..."):
                text = f"سائر... {text}"
            return text
        except Exception:
            return "سائر... الاتصال بمحرك الذكاء متعطل مؤقتًا، حاول بعد قليل."


ai_engine = AIEngine()
