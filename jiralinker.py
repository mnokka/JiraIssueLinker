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
import keyboard


start = time.clock()
__version__ = u"0.1" 



###################################################################
# should pass via parameters
# CODE CONFIGURATIONS
#####################################################################

# development vs production Jira
#ENV="DEV"
ENV="PROD"


# do only one operation for testing purposes
#ONCE="NO"
ONCE="YES"

# Used in JQL query 
CUSTOMFIELDDEV="customfield_10019"
CUSTOMFIELDEVID="cf[10019]"
CUSTOMFIELDPROD="customfield_10019"
CUSTOMFIELPRODID="cf[10019]"

if (ENV=="DEV"):
    CUSTOMFIELD=CUSTOMFIELDDEV
    CUSTOMFIELDID=CUSTOMFIELDEVID
elif (ENV=="PROD"):    
    CUSTOMFIELD=CUSTOMFIELDPROD
    CUSTOMFIELDID=CUSTOMFIELPRODID
   
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
    
    Press x anytime: Stop program
    
    """.format(__version__,sys.argv[0]))


    parser.add_argument('-v','--version', help='<Version>', action='store_true')   
    parser.add_argument('-w','--password', help='<JIRA password>')
    parser.add_argument('-u','--user', help='<JIRA username>')
    parser.add_argument('-s','--service', help='<JIRA service, like https://my.jira.com>')
    parser.add_argument('-l','--linked', help='<Jira linking target project ID to which source project issues to be linked, if (hardcoded) JQL rule matches') #add issue links to generated issues (target "into" linked issues must be allready in target jira)
    parser.add_argument('-p','--project', help='<JIRA source project ID')
    parser.add_argument('-d','--dry', help='Dry run mode ON|OFF . Default ON')

        
    args = parser.parse_args()
    
    if args.version:
        print 'Tool version: %s'  % __version__
        sys.exit(2)    

    
    JIRASERVICE = args.service or ''
    JIRAPROJECT = args.project or ''
    PSWD= args.password or ''
    USER= args.user or ''
    JIRALINKED=args.linked or ''
    DRYRUN=args.dry or 'ON' 
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
                        
    jql_query="Project = \'{0}\' and issuetype !=\'Drawings for Approval Remark\' ".format(JIRAPROJECT) # drop subtask off from first query   
    print "Used query:{0}".format(jql_query)
                        
    issue_list=jira.search_issues(jql_query, maxResults=4000)
    
    #required for plan b, runtime same as used method
    #allfields = jira.fields()
    #nameMap = {jira.field['name']:jira.field['id'] for jira.field in allfields}             
                        
    if len(issue_list) >= 1:
        COUNTER=1
        for issue in issue_list:
            #logging.debug("One issue returned for query")
            logging.debug("{0}:  Issue investigated ==========> {1}".format(COUNTER,issue))
            COUNTER=COUNTER+1
            #data="{0}".format(SourceCustomField)
            #mydata=data
            #kissa=issue.raw["fields"]["customfield_10019"]
            kissa=issue.raw["fields"]["{0}".format(CUSTOMFIELD)]
            types=issue.raw["fields"]["issuetype"]
            #koira=issue.custom_field_option(customfield_10019)
            # plan b , works
            #koira=getattr(issue.fields, nameMap["Drawing Number"])
            #logging.debug("koira==> {0}".format(koira))
            if kissa !=None:
                logging.debug("Tracked custom field value ==> {0}".format(kissa))
                OrinalIssueType=types.get("name")
                logging.debug("Tracked's issuetype ==> {0}".format(OrinalIssueType))
            
                regex = r"(D)(\.)(\d\d\d)(.*)"   # custom field wished value:  D.396.4600.401.036
                match = re.search(regex, kissa)
                
                if (match):
                    ProjectNumber=match.group(3)
                    logging.debug ("Matched:   ProjectNumber:{0}".format(ProjectNumber))
                
                    #OLDPROJECTNUMBER
                    OldProjectValue=str(kissa)
                    OldProjectValue=OldProjectValue.replace(str(ProjectNumber),str(OLDPROJECTNUMBER)) # D.396.4600.401.036 ---> D.394.4600.401.036
                    logging.debug ("Generated customfield tracking JQL:  OldProjectValue:{0}".format(OldProjectValue))
                
                    jql_query2="Project = \'{0}\' and \'{1}\' ~  \'{2}\'  ".format(JIRALINKED,CUSTOMFIELDID,OldProjectValue)
                    logging.debug ("JQL query:{0}".format(jql_query2))
                        
                    issue_list2=jira.search_issues(jql_query2)
                    logging.debug ("issue_list2:{0}".format(issue_list2))
                    
                    #logging.debug ("DRYRUN:{0}".format(DRYRUN))
                    # Check all issues matched the secondary JQL query (with modified custom field value)
                    if len(issue_list2) >= 1:
                        for issue2 in issue_list2:
                            LINK=False
                            if (DRYRUN=="ON" or DRYRUN=="OFF"):
                                #logging.debug("DRYRUN: WOULD LIKE TO LINK {0} ==> {1}".format(issue,issue2))
                                types2=issue2.raw["fields"]["issuetype"]
                                FoundIssueType=types2.get("name")
                                #
                                #logging.debug("FoundIssueType==> {0}".format(FoundIssueType))
                                #logging.debug("OrinalIssueType ==> {0}".format(OrinalIssueType))  
                                if (FoundIssueType != OrinalIssueType or ("Remark" in OrinalIssueType  )):  # Remarks (subtasks) not part of linking (iether source or target)
                                    logging.debug("....Skipping this match (Remark or different types): {0}".format(issue2))
                                    LINK=False
                                else:
                                    logging.debug("OK, same issutypes")
                                    
                                    #logging.debug("DRYRUN: WOULD LIKE TO LINK {0} ==> {1}".format(issue,issue2))
                                    if (issue2.fields.issuelinks): 
                                        #logging.debug("HIT: LINKS FOUND, NO OPERATIONS DONE")
                                        for link in issue2.fields.issuelinks:
                                            names=link.type.name
                                            #logging.debug("link id:{0} name:{1}".format(link,names)) #cloners
                                            if (names=="cloners"):
                                                logging.debug("cloners link , no actions")
                                                LINK=False
                                            else: 
                                                #logging.debug("action can be done")
                                                #logging.debug("DRYRUN: WOULD LIKE TO LINK {0} ==> {1}".format(issue,issue2))
                                                LINK=True
                                    else:
                                        logging.debug("No links found.")
                                        LINK=True
                                     
                                    
                                    if (LINK==True):
                                        if (DRYRUN=="ON"):
                                            logging.debug("DRYRUN: WOULD LIKE TO LINK {0} ==> {1}".format(issue,issue2))
                                            LINK=False
                                        elif (DRYRUN=="OFF"):
                                            logging.debug("--REAL EXECUTION MODE ---")   
                                    else:
                                        LINK=False                           
                    else:
                        logging.debug("NOTHING: No issues to be linked found")                       
                else:
                    print "ERROR: No match for ProjectNumber, skipping this issue !!!!"
            else:
                    print "ERROR: NULL  value for customfield , skipping this issue !!!!"
            

                
            logging.debug("---------------------------------------------------------------------------------------------------")
            if (keyboard.is_pressed("x")):
                logging.debug("x pressed, stopping now")
                break
            
            if (ONCE=="YES"):
                logging.debug("ONCE flag active, stopping now")
                break   
            
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
    
     

    
    
if __name__ == '__main__':
    main()
    
    
    
    

    
    
    