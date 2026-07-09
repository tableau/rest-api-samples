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
@XmlType(name = "siteType", propOrder = { "usage" })
public class SiteType {

    protected SiteType.Usage usage;
    @XmlAttribute(name = "id")
    protected String id;
    @XmlAttribute(name = "name")
    protected String name;
    @XmlAttribute(name = "contentUrl")
    protected String contentUrl;
    @XmlAttribute(name = "adminMode")
    protected String adminMode;
    @XmlAttribute(name = "userQuota")
    protected BigInteger userQuota;
    @XmlAttribute(name = "storageQuota")
    protected BigInteger storageQuota;
    @XmlAttribute(name = "disableSubscriptions")
    protected Boolean disableSubscriptions;
    @XmlAttribute(name = "state")
    protected String state;

    public SiteType.Usage getUsage() { return usage; }
    public void setUsage(SiteType.Usage value) { this.usage = value; }
    public String getId() { return id; }
    public void setId(String value) { this.id = value; }
    public String getName() { return name; }
    public void setName(String value) { this.name = value; }
    public String getContentUrl() { return contentUrl; }
    public void setContentUrl(String value) { this.contentUrl = value; }
    public String getAdminMode() { return adminMode; }
    public void setAdminMode(String value) { this.adminMode = value; }
    public BigInteger getUserQuota() { return userQuota; }
    public void setUserQuota(BigInteger value) { this.userQuota = value; }
    public BigInteger getStorageQuota() { return storageQuota; }
    public void setStorageQuota(BigInteger value) { this.storageQuota = value; }
    public Boolean isDisableSubscriptions() { return disableSubscriptions; }
    public void setDisableSubscriptions(Boolean value) { this.disableSubscriptions = value; }
    public String getState() { return state; }
    public void setState(String value) { this.state = value; }

    @XmlAccessorType(XmlAccessType.FIELD)
    @XmlType(name = "")
    public static class Usage {

        @XmlAttribute(name = "numUsers", required = true)
        @XmlSchemaType(name = "nonNegativeInteger")
        protected BigInteger numUsers;
        @XmlAttribute(name = "storage", required = true)
        @XmlSchemaType(name = "nonNegativeInteger")
        protected BigInteger storage;

        public BigInteger getNumUsers() { return numUsers; }
        public void setNumUsers(BigInteger value) { this.numUsers = value; }
        public BigInteger getStorage() { return storage; }
        public void setStorage(BigInteger value) { this.storage = value; }
    }
}
