from datetime import datetime
from rfc3339 import rfc3339
from suds.client import Client as SudsClient

import hmac
import hashlib

def sign(message, encryption_key):
    digest = hmac.new(encryption_key, message, hashlib.sha1)
    return digest.hexdigest().lower()

class Client(object):

    """
    Wrapper of the Marketo SOAP Api
    """

    MARKETO_WSDL = 'http://app.marketo.com/soap/mktows/2_2?WSDL'
    """Url of the Marketo wsdl file"""

    suds_types = []
    """List of the Marketo SOAP Api types"""
    suds_methods = []
    """List of the Marketo SOAP Api methods"""
    soap_endpoint = None
    """Marketo SOAP endpoint"""
    user_id = None
    """Marketo SOAP user ID"""
    encryption_key = None
    """Marketo SOAP encryption key"""
    suds_client = None
    """Consolidated API for consuming web services"""


    def __init__(self, soap_endpoint, user_id, encryption_key):
        """
        Instantiate the suds client and add the SOAP types and methods to the list of attributes
        How to get the Marketo SOAP parameters: See page 4 of the Marketo SOAP Api doc.
        """
        self.soap_endpoint = soap_endpoint
        self.user_id = user_id
        self.encryption_key = encryption_key

        self.suds_client = SudsClient(Client.MARKETO_WSDL,
                location=soap_endpoint)
        # Make easy the access to the types and methods
        for suds_type in self.suds_client.sd[0].types:
            self.suds_types.append(suds_type[0].name)
        for suds_method in self.suds_client.sd[0].service.ports[0].binding.operations:
            self.suds_methods.append(suds_method)

    def __getattribute__(self, name):
        """
        Lookup SOAP types and methods first.
        If the attribute is not a SOAP type or method, try to return an attribute of the class.
        """
        if name not in ('suds_types', 'suds_methods') and name in self.suds_types:
            # if the attribute is one of the SOAP types
            return self.suds_client.factory.create(name)
        elif name not in ('suds_types', 'suds_methods') and name in self.suds_methods:
            # if the attribute is one of the SOAP methods
            return self.suds_client.service.__getattr__(name)
        else:
            return super(Client, self).__getattribute__(name)

    def set_header(self):
        """
        Set the header of the SOAP request with the required parameters.
        See page 6 of the Marketo SOAP Api doc.
        """
        authentication_header = self.AuthenticationHeaderInfo
        timestamp = rfc3339(datetime.utcnow(), utc=True, use_system_timezone=False)
        authentication_header.requestSignature = sign(timestamp + self.user_id, self.encryption_key)
        authentication_header.mktowsUserId = self.user_id
        authentication_header.requestTimestamp = timestamp
        self.suds_client.set_options(soapheaders=authentication_header)

    def build_lead_record(self, email, attributes):
        lead_record = self.LeadRecord
        lead_record.Email = email
        lead_attributes_list = self.ArrayOfAttribute
        for attr in attributes:
            attribute = self.Attribute
            attribute.attrName, attribute.attrType, attribute.attrValue = attr
            lead_attributes_list.attribute.append(attribute)
        lead_record.leadAttributeList = lead_attributes_list
        return lead_record

    def call_service(self, name, *args, **kwargs):
        """Set the header before calling the soap service
        :param name: name of the soap method to call
        :param *args: list of arguments
        :param **kwargs: list of keyword arguments
        """
        self.set_header()
        return self.__getattribute__(name)(*args, **kwargs)
    
    def get_lead(self, keyValue, keyType):
        lead_key = self.LeadKey
        if keyType == 'Email':
            lead_key.keyType = self.LeadKeyRef.EMAIL
        if keyType == 'Cookie':
            lead_key.keyType = self.LeadKeyRef.COOKIE
        if keyType == 'IDNUM':
            lead_key.keyType = self.LeadKeyRef.IDNUM
        lead_key.keyValue = keyValue
        return self.call_service('getLead', lead_key)

    def get_lead_IDNUM(self, num):
        ID = self.LeadKey
        ID.keyType = self.LeadKeyRef.IDNUM
        ID.keyValue = num
        return self.call_service('getLead', ID)
    
    def get_lead_by_cookie(self, cook):
        cookie = self.LeadKey
        cookie.keyType = self.LeadKeyRef.COOKIE
        cookie.keyValue = cook
        return self.call_service('getLead', cookie)

    def sync_lead(self, email, attributes, return_lead=False):
        """
        :param email: email address of the lead to sync
        :param attributes: list of attributes as tuples
            format: ((Name, Type, Value), )
            example: (('FirstName', 'string', 'Spong'), ('LastName', 'string', 'Bob'))
        :param return_lead: If set to true, complete lead record will be returned. Default: False
        :return ResultSyncLead
        """
        lead_record = self.build_lead_record(email, attributes)
        return self.call_service('syncLead', lead_record, return_lead)

    def sync_multiple_leads(self, lead_list, dedup_enabled=True):
        """
        :param lead_record_list: List of tuples (email_address, attributes)
        :param dedup_enabled: If set to true, de-duplicate lead record on email address. Default: True
        :return ResultSyncMultipleLeads
        """
        lead_record_list = self.ArrayOfLeadRecord
        for lead in lead_list:
            lead_record_list.leadRecord.append(self.build_lead_record(lead[0], lead[1]))
        return self.call_service('syncMultipleLeads', lead_record_list, dedup_enabled)

    def request_campaign(self, source=None, campaign_id=None,
            lead_list=[], program_name=None, campaign_name=None,
            program_token_list=None):
        """
        :param source: ReqCampSourceType - Enumeration defined in WSDL
        :param campaign_id: integer - Optional: Marketo system ID (can use campaignName instead)
        :param campaign_name: string - Optional: Campaign name if ID not used
        :param lead_list: list of tuples:
            format: ((KeyType, KeyValue), )
            example: (("EMAIL", "a@b.com"), ("EMAIL", "c@b.com"))
            KeyType is a LeadKeyRef - Enumeration defined in WSDL
                example: self.LeadKeyRef.EMAIL
        :param program_name: string - Optional: Only required if using tokens
        :param program_token_list - Array of My Tokens to be used in campaign
        """
        source = source or self.ReqCampSourceType.MKTOWS
        lead_list_keys = self.ArrayOfLeadKey
        for lead in lead_list:
            lead_key = self.LeadKey
            lead_key.keyType.value, lead_key.keyValue = lead
            lead_list_keys.leadKey.append(lead_key)
        return self.call_service('requestCampaign', source, campaign_id,
            lead_list_keys, program_name, campaign_name, program_token_list)
        
    def merge_leads(self, winningleadIDnum, losingleadsIDnum):
        """
        I should make this more portable lol.
        :param winningleadkeylist: Type is ArrayofAttributes list of attributes as tuples
            format: ((Name, Type, Value), )
            example: (('FirstName', 'string', 'Spong'), ('LastName', 'string', 'Bob'))
        :param losingleads: Type is ArrayOfKeyList is an array of ArrayofAttributes
            example:[(('FirstName', 'string', 'Spong'), ('LastName', 'string', 'Bob')), 
                    (('FirstName', 'string', 'Spong'), ('LastName', 'string', 'Bob')),...]
        """
        win = self.__getattribute__('Attribute')
        win.attrName = 'IDNUM'
        win.attrValue = winningleadIDnum
        winning_lead_key_list = self.__getattribute__('ArrayOfAttribute')
        winning_lead_key_list.attribute.append(win)
        try:
            lose = self.__getattribute__('Attribute')
            lose.attrName = 'IDNUM'
            lose.attrValue = losingleadsIDnum
            losing_lead_key_list = self.__getattribute__('ArrayOfKeyList')
            attr = self.__getattribute__('ArrayOfAttribute')
            losing_lead_key_list.keyList.append(attr)
            losing_lead_key_list.keyList[0].attribute.append(lose)
        except:
            pass
        return self.call_service('mergeLeads', winning_lead_key_list, losing_lead_key_list)

    def get_lead_activity(self, keyval, keytype, acttype):
        """
        key and type.
        :param cookie: the marketo cookie
        I'll take this cookie and get all the lead activity
        :param type: can either be None, Email Activity, Personal Information, Website Activity, Score, Interesting Moments
        if it is personal information then I am probably going to have to do a getlead call with cookie into a getlead call with email to attempt to
        get duplicates or whatever. For now, if personal information I return true.
        """
        print acttype
        LeadKey = self.__getattribute__('LeadKey')
        ActivityType = self.__getattribute__('ActivityTypeFilter')
        #temporary leadkey keytype decision maker for actually having data
        LeadKey.keyValue = keyval
        LeadKey.keyType = keytype
        if acttype == 'Website Activity':
            ActivityType.includeTypes.activityType.append('VisitWebpage')
            ActivityType.includeTypes.activityType.append('ClickLink')
            ActivityType.includeTypes.activityType.append('FillOutForm')
        elif acttype == 'Email Activity':
            ActivityType.includeTypes.activityType.append('SendEmail')
            #ActivityType.includeTypes.activityType.append('EmailDelivered')
            ActivityType.includeTypes.activityType.append('EmailBounced') 
            ActivityType.includeTypes.activityType.append('UnsubscribeEmail')
            ActivityType.includeTypes.activityType.append('OpenEmail')
            ActivityType.includeTypes.activityType.append('ClickEmail')
            ActivityType.includeTypes.activityType.append('OpenSalesEmail')
            ActivityType.includeTypes.activityType.append('ClickSalesEmail')
            #ActivityType.includeTypes.activityType.append('ReceiveSalesEmail')
        elif acttype == 'Score':
            ActivityType.includeTypes.activityType.append('ChangeScore')
        elif acttype == 'Interesting Moments':
            ActivityType.includeTypes.activityType.append('InterestingMoment')
        else:
            print "test"  
        return self.call_service('getLeadActivity', LeadKey, ActivityType)
