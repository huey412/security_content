import os
import sys

from pydantic import ValidationError
from dataclasses import dataclass

from bin.contentctl_project.contentctl_core.domain.entities.enums.enums import SecurityContentProduct
from bin.contentctl_project.contentctl_core.domain.entities.enums.enums import SecurityContentType
from bin.contentctl_project.contentctl_core.application.builder.basic_builder import BasicBuilder
from bin.contentctl_project.contentctl_core.application.builder.detection_builder import DetectionBuilder
from bin.contentctl_project.contentctl_core.application.builder.story_builder import StoryBuilder
from bin.contentctl_project.contentctl_core.application.builder.baseline_builder import BaselineBuilder
from bin.contentctl_project.contentctl_core.application.builder.investigation_builder import InvestigationBuilder
from bin.contentctl_project.contentctl_core.application.builder.playbook_builder import PlaybookBuilder
from bin.contentctl_project.contentctl_core.application.builder.director import Director
from bin.contentctl_project.contentctl_core.application.factory.utils.utils import Utils
from bin.contentctl_project.contentctl_core.domain.entities.link_validator import LinkValidator

@dataclass(frozen=True)
class FactoryInputDto:
    input_path: str
    basic_builder: BasicBuilder
    detection_builder: DetectionBuilder
    story_builder: StoryBuilder
    baseline_builder: BaselineBuilder
    investigation_builder: InvestigationBuilder
    playbook_builder: PlaybookBuilder
    director: Director
    attack_enrichment: dict
    force_cached_or_offline: bool = True
    

@dataclass()
class FactoryOutputDto:
     detections: list
     stories: list
     baselines: list
     investigations: list
     playbooks: list
     deployments: list
     macros: list
     lookups: list
     tests: list


class Factory():
     input_dto: FactoryInputDto
     output_dto: FactoryOutputDto


     def __init__(self, output_dto: FactoryOutputDto) -> None:
        self.output_dto = output_dto


     def execute(self, input_dto: FactoryInputDto) -> None:
          self.input_dto = input_dto
          print("Creating Security Content - ESCU. This may take some time...")
          # order matters to load and enrich security content types
          self.createSecurityContent(SecurityContentType.unit_tests)
          self.createSecurityContent(SecurityContentType.lookups)
          self.createSecurityContent(SecurityContentType.macros)
          self.createSecurityContent(SecurityContentType.deployments)
          self.createSecurityContent(SecurityContentType.baselines)
          self.createSecurityContent(SecurityContentType.investigations)
          self.createSecurityContent(SecurityContentType.playbooks)
          self.createSecurityContent(SecurityContentType.detections)
          self.createSecurityContent(SecurityContentType.stories)
          LinkValidator.print_link_validation_errors()
          

     def createSecurityContent(self, type: SecurityContentType) -> list:
          
          objects = []
          if type == SecurityContentType.deployments:
               files = Utils.get_all_yml_files_from_directory(os.path.join(self.input_dto.input_path, str(type.name), 'ESCU'))
          elif type == SecurityContentType.unit_tests:
               files = Utils.get_all_yml_files_from_directory(os.path.join(self.input_dto.input_path, 'tests'))
          else:
               files = Utils.get_all_yml_files_from_directory(os.path.join(self.input_dto.input_path, str(type.name)))
          
          validation_error_found = False
          
          #Code below us commented out, but allows threaded construction of detections
          #No issues have been observed running construction in parallel
          '''
          import copy
          import threading
          NUM_THREADS = 1
          
          def make_detections_thread(index:int):
               my_dto = copy.deepcopy(self.input_dto)
               for i in range(index, len(files), NUM_THREADS):
                    file = files[i]
                    if 'ssa__' in file:
                         continue
                    try:
                         if type == SecurityContentType.lookups:
                              my_dto.director.constructLookup(my_dto.basic_builder, file)
                              self.output_dto.lookups.append(my_dto.basic_builder.getObject())
                         
                         elif type == SecurityContentType.macros:
                              my_dto.director.constructMacro(my_dto.basic_builder, file)
                              self.output_dto.macros.append(my_dto.basic_builder.getObject())
                         
                         elif type == SecurityContentType.deployments:
                              my_dto.director.constructDeployment(my_dto.basic_builder, file)
                              self.output_dto.deployments.append(my_dto.basic_builder.getObject())
                         
                         elif type == SecurityContentType.playbooks:
                              my_dto.director.constructPlaybook(my_dto.playbook_builder, file)
                              self.output_dto.playbooks.append(my_dto.playbook_builder.getObject())                    
                         
                         elif type == SecurityContentType.baselines:
                              my_dto.director.constructBaseline(my_dto.baseline_builder, file, self.output_dto.deployments)
                              baseline = my_dto.baseline_builder.getObject()
                              self.output_dto.baselines.append(baseline)
                         
                         elif type == SecurityContentType.investigations:
                              my_dto.director.constructInvestigation(my_dto.investigation_builder, file)
                              investigation = my_dto.investigation_builder.getObject()
                              self.output_dto.investigations.append(investigation)

                         elif type == SecurityContentType.stories:
                              my_dto.director.constructStory(my_dto.story_builder, file, 
                                   self.output_dto.detections, self.output_dto.baselines, self.output_dto.investigations)
                              story = my_dto.story_builder.getObject()
                              self.output_dto.stories.append(story)
                    
                         elif type == SecurityContentType.detections:
                              my_dto.director.constructDetection(my_dto.detection_builder, file, 
                                   self.output_dto.deployments, self.output_dto.playbooks, self.output_dto.baselines,
                                   self.output_dto.tests, my_dto.attack_enrichment, self.output_dto.macros,
                                   self.output_dto.lookups, my_dto.force_cached_or_offline)
                              detection = my_dto.detection_builder.getObject()
                              self.output_dto.detections.append(detection)
                    
                         elif type == SecurityContentType.unit_tests:
                              my_dto.director.constructTest(my_dto.basic_builder, file)
                              test = my_dto.basic_builder.getObject()
                              self.output_dto.tests.append(test)
                    
                    except ValidationError as e:
                         print('\nValidation Error for file ' + file)
                         print(e)
                         validation_error_found = True
                    
               

          builder_threads = []
          
          for t in range(NUM_THREADS):
               thread = threading.Thread(target=make_detections_thread,args=(t,))
               thread.start()
               builder_threads.append(thread)
          
          for thread in builder_threads:
               thread.join()
          '''
          
          #Non threaded, production version of the construction code
          files_without_ssa = [f for f in files if 'ssa___' not in f]
          for index,file in enumerate(files_without_ssa):
          
               #Index + 1 because we are zero indexed, not 1 indexed.  This ensures
               # that printouts end at 100%, not some other number 
               progress_percent = ((index+1)/len(files_without_ssa)) * 100
               try:
                    if type == SecurityContentType.lookups:
                         print(f"\r{'Lookups Progress'.rjust(23)}: [{progress_percent:3.0f}%]...", end="", flush=True)
                         self.input_dto.director.constructLookup(self.input_dto.basic_builder, file)
                         self.output_dto.lookups.append(self.input_dto.basic_builder.getObject())
                    
                    elif type == SecurityContentType.macros:
                         print(f"\r{'Playbooks Progress'.rjust(23)}: [{progress_percent:3.0f}%]...", end="", flush=True)
                         self.input_dto.director.constructMacro(self.input_dto.basic_builder, file)
                         self.output_dto.macros.append(self.input_dto.basic_builder.getObject())
                    
                    elif type == SecurityContentType.deployments:
                         print(f"\r{'Deployments Progress'.rjust(23)}: [{progress_percent:3.0f}%]...", end="", flush=True)
                         self.input_dto.director.constructDeployment(self.input_dto.basic_builder, file)
                         self.output_dto.deployments.append(self.input_dto.basic_builder.getObject())
                    
                    elif type == SecurityContentType.playbooks:
                         print(f"\r{'Playbooks Progress'.rjust(23)}: [{progress_percent:3.0f}%]...", end="", flush=True)
                         self.input_dto.director.constructPlaybook(self.input_dto.playbook_builder, file)
                         self.output_dto.playbooks.append(self.input_dto.playbook_builder.getObject())                    
                    
                    elif type == SecurityContentType.baselines:
                         print(f"\r{'Baselines Progress'.rjust(23)}: [{progress_percent:3.0f}%]...", end="", flush=True)
                         self.input_dto.director.constructBaseline(self.input_dto.baseline_builder, file, self.output_dto.deployments)
                         baseline = self.input_dto.baseline_builder.getObject()
                         self.output_dto.baselines.append(baseline)
                    
                    elif type == SecurityContentType.investigations:
                         print(f"\r{'Investigations Progress'.rjust(23)}: [{progress_percent:3.0f}%]...", end="", flush=True)
                         self.input_dto.director.constructInvestigation(self.input_dto.investigation_builder, file)
                         investigation = self.input_dto.investigation_builder.getObject()
                         self.output_dto.investigations.append(investigation)

                    elif type == SecurityContentType.stories:
                         print(f"\r{'Stories Progress'.rjust(23)}: [{progress_percent:3.0f}%]...", end="", flush=True)
                         self.input_dto.director.constructStory(self.input_dto.story_builder, file, 
                              self.output_dto.detections, self.output_dto.baselines, self.output_dto.investigations)
                         story = self.input_dto.story_builder.getObject()
                         self.output_dto.stories.append(story)
               
                    elif type == SecurityContentType.detections:
                         print(f"\r{'Detections Progress'.rjust(23)}: [{progress_percent:3.0f}%]...", end="", flush=True)
                         self.input_dto.director.constructDetection(self.input_dto.detection_builder, file, 
                              self.output_dto.deployments, self.output_dto.playbooks, self.output_dto.baselines,
                              self.output_dto.tests, self.input_dto.attack_enrichment, self.output_dto.macros,
                              self.output_dto.lookups, self.input_dto.force_cached_or_offline)
                         detection = self.input_dto.detection_builder.getObject()
                         self.output_dto.detections.append(detection)
               
                    elif type == SecurityContentType.unit_tests:
                         print(f"\r{'Unit Tests Progress'.rjust(23)}: [{progress_percent:3.0f}%]...", end="", flush=True)
                         self.input_dto.director.constructTest(self.input_dto.basic_builder, file)
                         test = self.input_dto.basic_builder.getObject()
                         self.output_dto.tests.append(test)
               
               except ValidationError as e:
                    print('\nValidation Error for file ' + file)
                    print(e)
                    validation_error_found = True
          print("Done!")

          if validation_error_found:
               sys.exit(1)