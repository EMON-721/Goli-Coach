"""Plain-text CMS schema: reject executable/unknown fields and unbounded collections."""
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from typing import Literal
class Strict(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
class FAQ(Strict):
 question_bn:str=Field(min_length=1,max_length=300)
 question_en:str=Field(min_length=1,max_length=300)
 answer_bn:str=Field(min_length=1,max_length=3000)
 answer_en:str=Field(min_length=1,max_length=3000)
class Navigation(Strict):
 id:Literal['home','practice','sessions','drills']
 bn:str=Field(min_length=1,max_length=60)
 en:str=Field(min_length=1,max_length=60)
class Drill(Strict):
 id:str=Field(min_length=1,max_length=60,pattern=r'^[a-z0-9-]+$')
 kind:Literal['batting','bowling','both']
 name:str=Field(min_length=1,max_length=120)
 en:str=Field(min_length=1,max_length=120)
 time:int=Field(ge=1,le=120)
 tag:str=Field(min_length=1,max_length=60)
 tagEn:str=Field(min_length=1,max_length=60)
 desc:str=Field(min_length=1,max_length=3000)
 enDesc:str=Field(min_length=1,max_length=3000)
 steps:list[str]=Field(min_length=1,max_length=15)
 enSteps:list[str]=Field(min_length=1,max_length=15)
TEXT_FIELDS={'brand','hero_bn','hero_en','about_bn','about_en','cta_bn','cta_en','privacy_bn','privacy_en','terms_bn','terms_en','mission_bn','mission_en','team_bn','team_en'}
def validate_content(value):
 if not isinstance(value,dict) or not set(value)<=TEXT_FIELDS|{'faq','drills','navigation'}:raise ValueError('Unknown CMS fields')
 for key in TEXT_FIELDS & value.keys():
  if not isinstance(value[key],str) or len(value[key])>6000:raise ValueError('Text fields must be at most 6000 characters')
 for key,model,limit in [('faq',FAQ,30),('drills',Drill,50),('navigation',Navigation,4)]:
  if key not in value:continue
  if not isinstance(value[key],list) or not 1<=len(value[key])<=limit:raise ValueError('Invalid '+key+' collection size')
  try:value[key]=[model.model_validate(row).model_dump() for row in value[key]]
  except ValidationError as e:raise ValueError('Invalid '+key+' fields') from e
  if key in ['drills','navigation'] and len({r['id'] for r in value[key]})!=len(value[key]):raise ValueError('Duplicate IDs in '+key)
  if key=='navigation' and len(value[key])!=4:raise ValueError('Keep all four primary destinations')
  if key=='drills' and any(len(step)>1000 for row in value[key] for step in row['steps']+row['enSteps']):raise ValueError('Drill steps too long')
 return value
