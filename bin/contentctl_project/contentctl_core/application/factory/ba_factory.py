import os
import sys

from pydantic import ValidationError
from dataclasses import dataclass

from bin.contentctl_project.contentctl_core.domain.entities.enums.enums import SecurityContentType
from bin.contentctl_project.contentctl_core.application.builder.basic_builder import BasicBuilder
from bin.contentctl_project.contentctl_core.application.builder.detection_builder import DetectionBuilder
from bin.contentctl_project.contentctl_core.application.builder.story_builder import StoryBuilder
from bin.contentctl_project.contentctl_core.application.builder.director import Director
from bin.contentctl_project.contentctl_core.application.factory.utils.utils import Utils


@dataclass(frozen=True)
class BAFactoryInputDto:
    input_path: str
    basic_builder: BasicBuilder
    detection_builder: DetectionBuilder
    director: Director

@dataclass(frozen=True)
class BAFactoryOutputDto:
     detections: list
     tests: list

class BAFactory():
    input_dto: BAFactoryInputDto
    output_dto: BAFactoryOutputDto

    def __init__(self, output_dto: BAFactoryOutputDto) -> None:
        self.output_dto = output_dto

    def execute(self, input_dto: BAFactoryInputDto) -> None:
        self.input_dto = input_dto
        print("Creating Security Content - SSA. This may take some time...")
        self.createSecurityContent(SecurityContentType.unit_tests)
        self.createSecurityContent(SecurityContentType.detections)
        

        

    def createSecurityContent(self, type: SecurityContentType) -> list:
        objects = []
        if type == SecurityContentType.unit_tests:
            files = Utils.get_all_yml_files_from_directory(os.path.join(self.input_dto.input_path, 'tests'))
        else:
            files = Utils.get_all_yml_files_from_directory(os.path.join(self.input_dto.input_path, str(type.name)))

        validation_error_found = False

        files_with_ssa = [f for f in files if 'ssa___' in f]
        for index,file in enumerate(files_with_ssa):
          
            #Index + 1 because we are zero indexed, not 1 indexed.  This ensures
            # that printouts end at 100%, not some other number 
            progress_percent = ((index+1)/len(files_with_ssa)) * 100
        
            if 'ssa__' in file:
                progress_percent = ((index+1)/len(files_with_ssa)) * 100
                try:
                    if type == SecurityContentType.detections:
                        print(f"\r{'Detections Progress'.rjust(23)}: [{progress_percent:3.0f}%]...", end="", flush=True)
                        self.input_dto.director.constructDetection(self.input_dto.detection_builder, file, [], [], [], self.output_dto.tests, {}, [], [])
                        detection = self.input_dto.detection_builder.getObject()
                        if not detection.deprecated and not detection.experimental:
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