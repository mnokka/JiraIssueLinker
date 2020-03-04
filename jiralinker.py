# This utility tool use (hardcoded) JQL rules to decide if source project issue(s)
# shoult be linked to target project issue(s)
#
# mika.nokka1@gmail.com 11.2.2020

from jira import JIRA
from datetime import datetime
import logging as log
#import pandas 
import argparse
import getpass
import time
import sys, logging
from author import Authenticate  # no need to use as external command
from author import DoJIRAStuff
import openpyxl 
from collections import defaultdict
import re

start = time.clock()
__version__ = u"0.1" 



###################################################################
# should pass via parameters
# CODE CONFIGURATIONS
#####################################################################

# development vs production Jira
ENV="DEV"
#ENV="PROD"


# do only one operation for testing purposes
ONCE="NO"
#ONCE="YES"

# Used in JQL query 
CUSTOMFIELDDEV="customfield_10019"
CUSTOMFIELDPROD="XXXXX"


if (ENV=="DEV"):
    CUSTOMFIELD=CUSTOMFIELDDEV
elif (ENV=="PROD"):    
    CUSTOMFIELD=CUSTOMFIELDPROD
   
# used to JQL query "to which older project to link"    
OLDPROJECTNUMBER=394

    
# LOGGING LEVEL: DEBUG or INFO or ERROR
logging.basicConfig(level=logging.DEBUG) # IF calling from Groovy, this must be set logging level DEBUG in Groovy side order these to be written out

###########################################################################


def main():

    
    JIRASERVICE=u""
    JIRAPROJECT=u""
    PSWD=u''
    USER=u''
  

 
    parser = argparse.ArgumentParser(usage="""
    {1}    Version:{0}     -  mika.nokka1@gmail.com 
    
    USAGE:

    python jiralinker.py -u <USERNAME> -w <PASSWORD> -s https://MYJIRA.COM -p <SOURCEPROJECTID> -l <LINKABLEPROJECTID>
    
    """.format(__version__,sys.argv[0]))


    parser.add_argument('-v','--version', help='<Version>', action='store_true')   
    parser.add_argument('-w','--password', help='<JIRA password>')
    parser.add_argument('-u','--user', help='<JIRA username>')
    parser.add_argument('-s','--service', help='<JIRA service, like https://my.jira.com>')
    parser.add_argument('-l','--linked', help='<Jira linking target project ID to which source project issues to be linked, if (hardcoded) JQL rule matches') #add issue links to generated issues (target "into" linked issues must be allready in target jira)
    parser.add_argument('-p','--project', help='<JIRA source project ID')

        
    args = parser.parse_args()
    
    if args.version:
        print 'Tool version: %s'  % __version__
        sys.exit(2)    

    
    JIRASERVICE = args.service or ''
    JIRAPROJECT = args.project or ''
    PSWD= args.password or ''
    USER= args.user or ''
    JIRALINKED=args.linked or ''
    #RENAME= args.rename or ''
    #ASCII=args.ascii or ''
    
    # quick old-school way to check needed parameters
    if (JIRASERVICE=='' or PSWD=='' or USER=='' or JIRAPROJECT==''  or JIRALINKED==''):
        parser.print_help()
        print "args: {0}".format(args)
        sys.exit(2)

    
    
    Authenticate(JIRASERVICE,PSWD,USER)
    jira=DoJIRAStuff(USER,PSWD,JIRASERVICE)
    
   
    SourceCustomField="issue.fields.{0}".format(CUSTOMFIELD)
    logging.debug("Using sourceCustomField==> {0}".format(SourceCustomField))
                        
    jql_query="Project = \'{0}\'  or Project = \'{1}\' ".format(JIRAPROJECT,JIRALINKED)
    #print "Query:{0}".format(jql_query)
                        
    issue_list=jira.search_issues(jql_query)
    
    #required for plan b, runtime same as used method
    #allfields = jira.fields()
    #nameMap = {jira.field['name']:jira.field['id'] for jira.field in allfields}             
                        
    if len(issue_list) >= 1:
        for issue in issue_list:
            #logging.debug("One issue returned for query")
            logging.debug("ISSUE TO BE LINKED ==> {0}".format(issue))
            #data="{0}".format(SourceCustomField)
            #mydata=data
            
            #kissa=issue.raw["fields"]["customfield_10019"]
            kissa=issue.raw["fields"]["{0}".format(CUSTOMFIELD)]
            #koira=issue.custom_field_option(customfield_10019)
            
            # plan b , works
            #koira=getattr(issue.fields, nameMap["Drawing Number"])
            #logging.debug("koira==> {0}".format(koira))
            
            logging.debug("TRACKED CUSTOMFIELD VALUE==> {0}".format(kissa))
            
            
            regex = r"(D)(\.)(\d\d\d)(.*)"   # custom field wished value:  D.396.4600.401.036
            match = re.search(regex, kissa)
                
            if (match):
                ProjectNumber=match.group(3)
                logging.debug ("MATCH FOUND!!   ProjectNumber:{0}".format(ProjectNumber))
                
                #OLDPROJECTNUMBER
                OldProjectValue=str(kissa)
                OldProjectValue=OldProjectValue.replace(str(ProjectNumber),str(OLDPROJECTNUMBER)) # D.396.4600.401.036 ---> D.394.4600.401.036
                logging.debug ("Generated customfield for JQL:  OldProjectValue:{0}".format(OldProjectValue))
                
                
            else:
                print "ERROR: No match for ProjectNumber"
            
            
            
            logging.debug("------------------------------------------------------")
            
    #elif len(issue_list) > 1:
        #    logging.debug("ERROR ==> More than 1 issue was returned by JQL query")
        #    LINKEDISSUE="EMPTY"
    else:
        logging.debug("==> No issue(s) returned by JQL query")
        #LINKEDISSUE="EMPTY"
            #else:
            #    LINKEDISSUE="EMPTY"               
                        
             
                    
                    
            
                
             
         
                
    time.sleep(0.7) # prevent jira crashing for script attack
    if (ONCE=="YES"):
        print "ONCE testing mode ,stopping now"
        sys.exit(5) #testing do only once
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        #now excel has been prosessed
        
    end = time.clock()
    totaltime=end-start
    print "Time taken:{0} seconds".format(totaltime)
    print "*************************************************************************"
    sys.exit(0)
    




    
def CreateMitigationIssue(jira,JIRAPROJECT,SUMMARY,ISSUE_TYPE,PRIORITY,STATUS,USERNAME_ASSIGNEE,DESCRIPTION,MitigationCostsKeur,NEWSTATUS,ENV,DISCIPLINE,CAT):
    
    
    TRANSIT="None"
    jiraobj=jira
    project=JIRAPROJECT
    TASKTYPE="Task" #hardcoded

    print "Creating mitigation issue for JIRA project: {0}".format(project)
    
    issue_dict = {
    'project': {'key': JIRAPROJECT},
    'summary': str(SUMMARY),
    'description': str(DESCRIPTION),
    'issuetype': {'name': TASKTYPE},
    'priority': {'name': str(PRIORITY) }, 
    'assignee': {'name':USERNAME_ASSIGNEE},
        'customfield_14302' if (ENV =="DEV") else 'customfield_14216' : int(MitigationCostsKeur), # MitigationCostsKeur dev: 14302  prod: 14216

    }

    try:
        new_issue = jiraobj.create_issue(fields=issue_dict)
        print "===> Issue created OK:{0}".format(new_issue)
        if (NEWSTATUS != "To Do"): # status after cretion
            
            #map state to transit for Mitigation issues
            if (NEWSTATUS=="In Progress"):
                TRANSIT="Start Progress"
            if (NEWSTATUS=="Done"):
                TRANSIT="Done"
            
            
            print "Newstatus will be:{0}".format(NEWSTATUS)
            print "===> Executing transit:{0}".format(TRANSIT)
            jiraobj.transition_issue(new_issue, transition=TRANSIT)  # trantsit to state where it was in excel 
        else:
            print "Initial status found: {0}, nothing done".format(NEWSTATUS)
            
             
  
   
        
    except Exception,e:
        print("Failed to create JIRA object or transit problem, error: %s" % e)
        sys.exit(1)
    return new_issue    
    
     
def CreateRiskIssue(jira,JIRAPROJECT,SUMMARY,ISSUE_TYPE,PRIORITY,STATUS,USERNAME_ASSIGNEE,DESCRIPTION,MitigationCostsKeur,NEWSTATUS,ENV,DISCIPLINE,TYPE,RiskCost,CAT,TOLINKLIST,LINKS):
    
    print "=====>    Internal configuration:{0} , {1} , {2}".format(ENV, TYPE, CAT)
    print "Discipline:{0} ".format(DISCIPLINE)
    
    TRANSIT="NA"
    jiraobj=jira
    project=JIRAPROJECT
    TASKTYPE="Task" #hardcoded
    DISCIPLINEFIELD="None"

    print "Creating Risk issue for JIRA project: {0}".format(project)
    
    
    issue_dict = {
    'project': {'key': JIRAPROJECT},
    'summary': str(SUMMARY),
    'description': str(DESCRIPTION),
    'issuetype': {'name': TASKTYPE},
    'priority': {'name': str(PRIORITY) }, 
    #'resolution':{'id': '10100'},
    'assignee': {'name':USERNAME_ASSIGNEE}, 
    'customfield_14203' if (ENV =="DEV") else 'customfield_14208' : int(RiskCost),  # Risk Cost (Keur) dev: 14203  prod: 14208
   
    
    }

    try:
        new_issue = jiraobj.create_issue(fields=issue_dict)
        print "===> Issue created OK:{0}".format(new_issue)
        if (NEWSTATUS != "Proposed"): # status after cretion
            
            #map state to transit for Mitigation issues
            if (NEWSTATUS=="Threat"):
                TRANSIT="Threat"
            if (NEWSTATUS=="Realized"):
                TRANSIT="Realized"
            if (NEWSTATUS=="Eliminated"):
                TRANSIT="Eliminated"   
            if (NEWSTATUS=="No Action"):
                TRANSIT="No Action" # prod transt, dev transit was NoAction 
            
            print "Newstatus will be:{0}".format(NEWSTATUS)
            print "===> Executing transit:{0}".format(TRANSIT)
            jiraobj.transition_issue(new_issue, transition=TRANSIT)  # trantsit to state where it was in excel
        else:
            print "Initial status found: {0}, nothing done".format(NEWSTATUS)
            
        
        #only quikc way set drop down menus, creation did not work as dictionary in use (should have used multiple dictionaries....)
        if (ENV =="DEV" and CAT=="FIN"):
            DISCIPLINEFIELD="customfield_14223" # DisciplineF 
        elif (ENV =="DEV" and CAT=="SHIP"):
            DISCIPLINEFIELD="customfield_14328" #  DisciplineRM
        elif (ENV =="PROD" and CAT=="FIN"):
            DISCIPLINEFIELD="customfield_14210" # DisciplineF 
        elif (ENV =="PROD" and CAT=="SHIP"): 
            DISCIPLINEFIELD="customfield_14209" #  DisciplineRM
        else:
            print "ARGH ERRORS WTIH RISK DISCIPLINE FIELDS"    
        print "DISCIPLINE:{0}".format(DISCIPLINE)
        new_issue.update(fields={DISCIPLINEFIELD: {"id": "-1"}})  #   DISCIPLINE
        
        #print "new issue: {0}   linked issue:{1}".format(new_issue,LINKEDISSUE)
        LENGHT=len(TOLINKLIST)
        print "List of linked ones, length:{0}".format(LENGHT)
        if (LINKS and TOLINKLIST): # link only if requested and there is something to link
            
            for LINKEDISSUE in TOLINKLIST:
                print "Linking requested, doing: new issue: {0} --> is mitigated by --->  linked issue:{1}".format(new_issue,LINKEDISSUE) # linktype hardcoded
                time.sleep(0.5)
                jiraobj.create_issue_link("is mitigated by",new_issue,LINKEDISSUE,None) # last is comment field, skipping now
        else:
            print "No linking requested nor no links for this issue, skipping"

        
        
        
    except Exception,e:
        print("Failed to create JIRA object or transit problem, error: %s" % e)
        sys.exit(1)
    return new_issue   
    
    
if __name__ == '__main__':
    main()
    
    
    
    

    
    
    