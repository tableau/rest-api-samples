// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import java.math.BigInteger;
import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlAttribute;
import jakarta.xml.bind.annotation.XmlSchemaType;
import jakarta.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "groupType")
public class GroupType {

    @XmlAttribute(name = "externalUserEnabled")
    protected Boolean externalUserEnabled;
    @XmlAttribute(name = "id")
    protected String id;
    @XmlAttribute(name = "minimumSiteRole")
    protected SiteRoleType minimumSiteRole;
    @XmlAttribute(name = "name")
    protected String name;
    @XmlAttribute(name = "userCount")
    @XmlSchemaType(name = "nonNegativeInteger")
    protected BigInteger userCount;

    public Boolean getExternalUserEnabled() { return externalUserEnabled; }
    public void setExternalUserEnabled(Boolean value) { this.externalUserEnabled = value; }
    public String getId() { return id; }
    public void setId(String value) { this.id = value; }
    public SiteRoleType getMinimumSiteRole() { return minimumSiteRole; }
    public void setMinimumSiteRole(SiteRoleType value) { this.minimumSiteRole = value; }
    public String getName() { return name; }
    public void setName(String value) { this.name = value; }
    public BigInteger getUserCount() { return userCount; }
    public void setUserCount(BigInteger value) { this.userCount = value; }
}
