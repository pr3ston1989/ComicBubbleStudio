"""Repeated sales calls plus two whole-page checks, never creator names alone."""
import copy,json,re
from .geometry import intersection,area
from .promotion_audit import PROMOTION_PROMPT,CONFIRM_PROMPT
from .page_context import renumber_after_omission
def sale_evidence(document):
 if document['analysis'].get('page_context',{}).get('classification',{}).get('kind')=='character_profile':return None
 rows=[];hits=[]
 for check in document['analysis'].get('text_check',{}).get('regions',[]):
  cb=check.get('box')
  if not cb or len(cb)!=4:continue
  for row in check.get('ocr',[]):
   if row.get('score',0)<.85:continue
   rows.append(row);text=re.sub('[^a-z0-9]','',row.get('text','').lower())
   if re.fullmatch(r'(?:part|chapter)(?:[0-9]+|one|two|three|four|five|six|seven|eight|nine|ten|[ivxlcdm]+)',text):return None
   if not any(s in text for s in ('collectioninstores','instoresnow','onsalenow','availablewherever','buyitnow','ordertoday','preordernow')):continue
   b=row.get('box')
   if not b or len(b)!=4:continue
   x,y,xx,yy=cb;box=[x+b[0]*(xx-x),y+b[1]*(yy-y),x+b[2]*(xx-x),y+b[3]*(yy-y)]
   if any(intersection(box,h['box'])/max(1,min(area(box),area(h['box'])))>.7 for h in hits):continue
   hits.append(dict(text=row['text'],box=box))
 return dict(rows=rows,hits=hits) if len(hits)>=2 else None
def refine(image,document,semantic):
 if document.get('review',{}).get('verified') or not document['result']['bubbles']:return document
 evidence=sale_evidence(document)
 if not evidence:return document
 whole=image.copy();whole.thumbnail((1280,1600));bottom=image.crop((0,image.height//2,image.width,image.height));bottom.thumbnail((1100,900))
 first=semantic._ask([whole],PROMOTION_PROMPT+json.dumps([r['text'][:200] for r in evidence['rows'][:80]],ensure_ascii=False),100)
 if not isinstance(first,dict) or first.get('entire_page_is_real_world_promotion') is not True:return document
 second=semantic._ask([whole,bottom],CONFIRM_PROMPT,100)
 if not isinstance(second,dict) or second.get('advertising_layout_without_story') is not True:return document
 removed=[b['id'] for b in document['result']['bubbles']];snapshot=copy.deepcopy(document['result'])
 renumber_after_omission(document,set(removed))
 document['analysis']['retail_promotion_audit']=dict(original_result=snapshot,removed=removed,evidence=evidence,first=first,confirmation=second)
 document['review']['flags'].append('Pominięto potwierdzoną stronę oferty wydawniczej; wynik można przywrócić')
 return document
