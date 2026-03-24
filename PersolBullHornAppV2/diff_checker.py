from deepdiff import DeepDiff

class DiffChecker():

    def __init__(self, app_sdk):
        self.app_sdk = app_sdk

    TOP_LEVEL_FIELDS_WITHOUT_NESTING_AND_WITHOUT_LAST_ACTIVITY = {
            "candidateId",
            "title",
            "dateOfBirth",
            "visaStatuses",
            "address",
            "emails",
            "emails2",
            "phones",
            "gender",
            "firstName",
            "lastName",
            "skills",       # list of strings 
            "resumeContent" # dictionary
            }

    NOTES_FIELDS_USED_IN_MAPPING = {
        "cc",
        "creationTs", 
        "body", 
        "sender", 
        "noteType", 
        "creator"
        }

    EDUCATION_FIELDS_USED_IN_MAPPING = {
        "degree",
        "school",
        "startTs",
        "endTs",
        "location",
        "major",
        "description"
    }

    EXPERIENCE_FIELDS_USED_IN_MAPPING = {
        "company",
        "startTs",
        "title",
        "description",
        "location",
        "endTs",
        "isCurrent",
        "isInternal"
    }

    APPLICATION_FIELDS_USED_IN_MAPPING = {
        "applicationTs",
        "candidateId",
        "lastModifiedTs",
        "jobs", #CONDITIONAL 
        "applicationId",
        "currentStage", #CONDITIONAL 
        "status", #CONDITIONAL
        "reason",
        "source"
    }

    APPLICATION_CURRENT_STAGE_FIELDS_USED_IN_MAPPING = {
        "wfStage",
        "stageTs",
        "reason",
        "wfSubStage",
        "user"
    }

    APPLICATION_CURRENT_STAGE_USER_FIELDS_USED_IN_MAPPING = {
        "name",
        "email"
    }

    APPLICATION_JOB_DICT_USED_IN_MAPPING = {
        "name",
        "atsJobId"
    }

    def has_notes_diff_handler(self, ef_entry, mapped_ef_entry, entity_id):
        for note in ef_entry:
            for key in note.copy(): #cant edit the dict being iterated directly.
                if key not in self.NOTES_FIELDS_USED_IN_MAPPING:
                    note.pop(key)
        
        diff = DeepDiff(ef_entry, mapped_ef_entry, ignore_order=True)
        if diff != {}:
            self.app_sdk.log(f"has_notes_diff_handler entity_id : {entity_id} diff : {diff}")
            return True
        return False
    
    def has_education_diff_handler(self,ef_entry, mapped_ef_entry, entity_id):
        for education in ef_entry:
            for key in education.copy(): #cant edit the dict being iterated directly.
                if key not in self.EDUCATION_FIELDS_USED_IN_MAPPING:
                    education.pop(key)

        diff = DeepDiff(ef_entry, mapped_ef_entry, ignore_order = True)
        if diff != {}:
            self.app_sdk.log(f"education_diff_handler entity_id : {entity_id} diff : {diff}")
            return True
        return False

    def has_experience_diff_handler(self, ef_entry, mapped_ef_entry, entity_id):
        for experience in ef_entry:
            for key in experience.copy(): #cant edit the dict being iterated directly.
                if key not in self.EXPERIENCE_FIELDS_USED_IN_MAPPING:
                    experience.pop(key)

        diff = DeepDiff(ef_entry, mapped_ef_entry, ignore_order = True)
        if diff != {}:
            self.app_sdk.log(f"has_experience_diff_handler entity_id : {entity_id} diff : {diff}")
            return True
        return False

    def has_applications_diff_handler(self, ef_entry, mapped_ef_entry, entity_id):
        for application in ef_entry:
            for key in application.copy():
                if key not in self.APPLICATION_FIELDS_USED_IN_MAPPING:
                    application.pop(key)

                if key == 'currentStage': # currentStage is nested
                    currentStage = application[key]
                    
                    for currentStageKey in currentStage.copy():
                        if currentStageKey not in self.APPLICATION_CURRENT_STAGE_FIELDS_USED_IN_MAPPING:
                            currentStage.pop(currentStageKey)
                        
                        if currentStageKey == 'user':
                            currentStageUser = currentStage[currentStageKey]

                            for currentStageUserKey in currentStageUser.copy():
                                if currentStageUserKey not in self.APPLICATION_CURRENT_STAGE_USER_FIELDS_USED_IN_MAPPING:
                                    currentStageUser.pop(currentStageUserKey)

                if key == 'jobs':
                    #remove the extra fields from each job in the list of jobs
                    joblist = application['jobs'] # a list
                    for job in  joblist:
                        for jobkey in job:
                            if jobkey not in self.APPLICATION_JOB_DICT_USED_IN_MAPPING:
                                job.pop(jobkey)

                    #TODO sort the jobs by atsjobid but as per code only 1 entry goes in list, hence not sorting as of now.

        ef_entry_map = {}
        for entry in ef_entry:
            ef_entry_map[entry['applicationId']] = entry

        mapped_ef_entry_map = {}
        for entry in mapped_ef_entry:
            mapped_ef_entry_map[entry['applicationId']] = entry
        
        diff = {}

        for key in mapped_ef_entry_map:
            if key not in ef_entry_map:
                diff["Application doesnt exist in ef"] = key
                continue
            application_diff = DeepDiff(ef_entry_map[key], mapped_ef_entry_map[key], ignore_order=True )
            if application_diff != {}:
                 diff[key] = application_diff

        if diff != {}:
            self.app_sdk.log(f"has_applications_diff_handler entity_id : {entity_id} diff : {diff}")
            return True
        return False
        
    def is_top_level_diff(self, ef_data_subset, mapped_ef_data_from_bh, entity_id):
        
        ef_top_level = {}
        mapped_ef_top_level = {}

        for key in self.TOP_LEVEL_FIELDS_WITHOUT_NESTING_AND_WITHOUT_LAST_ACTIVITY:
            if key in ef_data_subset:
                ef_top_level[key] = ef_data_subset[key]
            if key in mapped_ef_data_from_bh:
                mapped_ef_top_level[key] = mapped_ef_data_from_bh[key]
        
        top_level_diff = DeepDiff(ef_top_level,mapped_ef_top_level, ignore_order=True)
        if top_level_diff != {}:
            self.app_sdk.log(f"entity_id : {entity_id} top_level_diff : {top_level_diff} ")
            return True
        return False

    
    def has_difference(self, ef_data, mapped_ef_data_from_bh, entity_id):
        self.app_sdk.log(f"Comparing for entity_id : {entity_id} ef_data : {ef_data} with mapped_ef_data_from_bh : {mapped_ef_data_from_bh}")
        try:
            # Not touching present flow if one or both are non due to api failure etc
            if not ef_data or not mapped_ef_data_from_bh:
                self.app_sdk.log(f"entity_id : {entity_id} ef_data or mapped_ef_data_from_bh is empty.")
                return True

            #need to only compare the subset being patched by BH in this call
            ef_data_subset = {}
            for key in mapped_ef_data_from_bh:
                if key in ef_data:
                    ef_data_subset[key] = ef_data[key]
            
            if self.is_top_level_diff(ef_data_subset, mapped_ef_data_from_bh, entity_id):
                return True

            notes_diff = self.has_notes_diff_handler(ef_data_subset.get('notes',[]), mapped_ef_data_from_bh.get('notes',[]), entity_id)
            if notes_diff:
                return True

            education_diff = self.has_education_diff_handler(ef_data_subset.get('education',[]) , mapped_ef_data_from_bh.get('education',[]), entity_id)
            if education_diff:
                return True

            experience_diff = self.has_experience_diff_handler(ef_data_subset.get('experience',[]) , mapped_ef_data_from_bh.get('experience',[]), entity_id)
            if experience_diff:
               return True
        
            application_diff = self.has_applications_diff_handler(ef_data_subset.get('applications',[]) , mapped_ef_data_from_bh.get('applications',[]), entity_id)
            if application_diff:
                return True
            
            # No Difference spotted finally.
            return False
        except Exception as ex:
            self.app_sdk.log(f"has_difference entity_id : {entity_id} exception : {str(ex)}")  
        # Current flow unaffected if some exception occured.
        return True

    