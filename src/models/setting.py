# setting.py
from pydantic import BaseModel

class Setting(BaseModel):
    id: str # settingin yani cevre ve mekanin id si, veritabani vb. islemleri icin user ile alakasiz.
    name: str # settingin ismi
    style: str # settingin tarzi (etc. medieval, teknolojik, latin, kuzeyli etc.)
    time: str # gectigi yuzyil, tam tarih veya donemi ifade edebilecek herhangi bir sey.
    location: str # genel dunyaya gore gorece konumu (mesela x ulkesinde veya y daglarinin eteginde veya bilmemne isimli konuma yakin gibi)
    environment: str # cevrenin genel siniflandirma bilgisi (mesela ormanlik, sehir, kasaba, sonsuzluk, uzay etc.)
    environment_details: str # cevrenin detayli betimlemesi ve tasviri (mesela sadece sehir demek yerine caddelerin betimlemesi, insanlarin ve binalarin tarzi etc.)
    social: str  # sosyal yapisi (mesela uzay ise yok dersin, ama mesela bir kasaba hakkinda insanlar, nufus, konusma tarzi, dusmancil, misafirperver, canli, sessiz gibi veya nasil olduklari)
    mood: str
    sensory_details: str
    info: list[str] # ek diger bilgiler (mesela burada olan gecmis savaslar veya baska bilgiler)
    experience: list[str] # burada hikayenin basindan sonra yasananlar (mesela 3 chapter once bir savas olduysa burasi yikilmis ve yanmissa bunun tasviri icin)
