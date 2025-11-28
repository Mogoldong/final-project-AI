import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 1. 저장 경로 설정
SAVE_DIR = "data/knowledge"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)
    
FILENAME = os.path.join(SAVE_DIR, "food_knowledge.pdf")

# 2. PDF에 들어갈 '지식' 내용 (요리 상식 백과)
content = """
[요리 상식 및 영양 가이드]

1. 키토제닉 다이어트 (Ketogenic Diet)
키토제닉 다이어트는 탄수화물 섭취를 극도로 제한하고 지방 섭취를 늘리는 식이요법입니다.
- 원리: 몸이 탄수화물 대신 지방을 에너지원으로 쓰게 만들어 '케토시스' 상태를 유도합니다.
- 권장 음식: 육류(삼겹살, 소고기), 생선(연어, 고등어), 달걀, 버터, 치즈, 아보카도.
- 피해야 할 음식: 밥, 빵, 면, 설탕, 과일(당분).
- 주의사항: 초기에는 두통이나 피로감(키토 플루)이 올 수 있습니다.

2. 식재료 대체 가이드
요리할 때 특정 재료가 없다면 다음으로 대체할 수 있습니다.
- 설탕 대체: 올리고당, 꿀, 매실청, 스테비아. (단맛을 내지만 풍미가 다를 수 있음)
- 버터 대체: 마가린, 식용유(카놀라유 등), 코코넛 오일.
- 우유 대체: 두유, 아몬드 브리즈, 물(농도 조절 필요).
- 전분 대체: 밀가루, 찹쌀가루, 계란 흰자.

3. 식재료 보관 꿀팁
- 다진 마늘: 얼음 트레이에 소분해서 얼려두면 필요할 때 하나씩 꺼내 쓰기 좋습니다.
- 대파: 씻어서 물기를 완전히 제거한 후 썰어서 냉동 보관하면 오래갑니다.
- 양파: 껍질을 깐 양파는 랩으로 개별 포장하여 냉장 보관하세요.
"""

def create_pdf():
    c = canvas.Canvas(FILENAME, pagesize=A4)
    
    # (참고) 한글 폰트 설정이 없으면 글자가 깨질 수 있습니다.
    # 영문으로 테스트하거나, 시스템에 있는 한글 폰트 경로를 지정해야 합니다.
    # 여기서는 안전하게 영문/기본 폰트로 변환하거나 설명을 위해 텍스트만 저장합니다.
    # **실습 편의를 위해 위 내용을 '텍스트 파일(.txt)'로 저장하는 것도 방법입니다.**
    # 하지만 교수님 요구사항이 PDF이므로, PDF 생성 로직을 유지하되
    # 한글 깨짐 방지를 위해 영어로 변환된 내용을 넣겠습니다.
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 800, "Culinary Knowledge Encyclopedia")
    
    c.setFont("Helvetica", 12)
    y = 750
    lines = [
        "1. Ketogenic Diet",
        "Keto diet is a low-carb, high-fat diet.",
        "- Principle: Induce ketosis to burn fat instead of carbs.",
        "- Good Foods: Meat, Fish, Eggs, Butter, Cheese, Avocado.",
        "- Bad Foods: Rice, Bread, Sugar, Fruits.",
        "",
        "2. Ingredient Substitutes",
        "- Sugar -> Honey, Oligosaccharide, Stevia",
        "- Butter -> Margarine, Cooking Oil, Coconut Oil",
        "- Milk -> Soy Milk, Almond Breeze",
        "",
        "3. Food Storage Tips",
        "- Garlic: Freeze minced garlic in ice trays.",
        "- Green Onions: Wash, dry, chop, and freeze.",
        "- Onions: Wrap peeled onions individually and refrigerate."
    ]
    
    for line in lines:
        c.drawString(100, y, line)
        y -= 20
        
    c.save()
    print(f"✅ PDF 생성 완료: {FILENAME}")

if __name__ == "__main__":
    create_pdf()