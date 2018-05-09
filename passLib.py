import ldap

LDAP_HOST = 'ldapmaster.cs.nsls2.local'
LDAP_PROVIDER_URL = 'ldaps://{0}'.format(LDAP_HOST)


LDAP_SUFFIX = 'dc=nsls2,dc=bnl,dc=gov'
LDAP_USUFFIX = 'ou=People'
LDAP_GSUFFIX = 'ou=Group'
LDAP_BASE_DN = '{0},{1}'.format(LDAP_USUFFIX, LDAP_SUFFIX)
LDAP_GROUP = '{0},{1}'.format(LDAP_GSUFFIX, LDAP_SUFFIX)



def get_ldap_connection():   
    conn = ldap.initialize(LDAP_PROVIDER_URL)
    return conn

def get_gid_per_groupname(groupname):
    """
    figure out what should be the gid from the
    :param groupname is "p'"=str(proposalid)
    :return:
    """
    CN = 'cn=' + groupname
    conn = get_ldap_connection()
    res_id = conn.search(LDAP_GROUP, ldap.SCOPE_SUBTREE, CN)
    (response, results) = conn.result(res_id, 0)  # 0 means one result at the time, for all result change for 1
    gid = results[0][1]['gidNumber'][0]
    return gid





#g = get_gid_per_groupname('p301022')

#In [43]: g
#Out[43]: '5993'
