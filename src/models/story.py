# story.py
from pydantic import BaseModel
from src.models.story_metadata import StoryMetadata
from src.models.pov import PovType

class Story(BaseModel):
    id: str
    story_metadata: StoryMetadata
    world_id: str # buraya icinde gectigi evren/dunya referansi gelecek, o modeli ekleyince. mesela ayni evrende birden fazla karakter yazabilirsin! mesela birinde ayni cevreyi kullanip yuzyillar oncesinden anlatirsin, sonra baska karakterler ile ayni cevrede ayni evrende baska bir hikaye... hikaye referanslari da verebilirsin belki.
    pov: PovType # bakis acisi
    # belki world vb. metadata da degil burada olmali, metadata daha cok metadata olarak kalmali.
    chapters: list[str]

    def serialize(self) -> str:
        """
        Sonradan ekleyecegim function.
        mesela kitabi dosyaya yazdirmak icin. cikti vb. almak icin.
        filetype de alabilir.
        """
        pass
