// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlAttribute;
import jakarta.xml.bind.annotation.XmlSchemaType;
import jakarta.xml.bind.annotation.XmlType;
import javax.xml.datatype.XMLGregorianCalendar;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "userType")
public class UserType {

    @XmlAttribute(name = "authSetting")
    protected String authSetting;
    @XmlAttribute(name = "contentAdmin")
    protected Boolean contentAdmin;
    @XmlAttribute(name = "email")
    protected String email;
    @XmlAttribute(name = "externalAuthUserId")
    protected String externalAuthUserId;
    @XmlAttribute(name = "fullName")
    protected String fullName;
    @XmlAttribute(name = "id")
    protected String id;
    @XmlAttribute(name = "language")
    protected String language;
    @XmlAttribute(name = "lastLogin")
    @XmlSchemaType(name = "dateTime")
    protected XMLGregorianCalendar lastLogin;
    @XmlAttribute(name = "locale")
    protected String locale;
    @XmlAttribute(name = "name")
    protected String name;
    @XmlAttribute(name = "ownsContent")
    protected Boolean ownsContent;
    @XmlAttribute(name = "password")
    protected String password;
    @XmlAttribute(name = "publish")
    protected Boolean publish;
    @XmlAttribute(name = "siteRole")
    protected SiteRoleType siteRole;
    @XmlAttribute(name = "suppressGettingStarted")
    protected Boolean suppressGettingStarted;

    public String getAuthSetting() { return authSetting; }
    public void setAuthSetting(String value) { this.authSetting = value; }
    public Boolean getContentAdmin() { return contentAdmin; }
    public void setContentAdmin(Boolean value) { this.contentAdmin = value; }
    public String getEmail() { return email; }
    public void setEmail(String value) { this.email = value; }
    public String getExternalAuthUserId() { return externalAuthUserId; }
    public void setExternalAuthUserId(String value) { this.externalAuthUserId = value; }
    public String getFullName() { return fullName; }
    public void setFullName(String value) { this.fullName = value; }
    public String getId() { return id; }
    public void setId(String value) { this.id = value; }
    public String getLanguage() { return language; }
    public void setLanguage(String value) { this.language = value; }
    public XMLGregorianCalendar getLastLogin() { return lastLogin; }
    public void setLastLogin(XMLGregorianCalendar value) { this.lastLogin = value; }
    public String getLocale() { return locale; }
    public void setLocale(String value) { this.locale = value; }
    public String getName() { return name; }
    public void setName(String value) { this.name = value; }
    public Boolean getOwnsContent() { return ownsContent; }
    public void setOwnsContent(Boolean value) { this.ownsContent = value; }
    public String getPassword() { return password; }
    public void setPassword(String value) { this.password = value; }
    public Boolean getPublish() { return publish; }
    public void setPublish(Boolean value) { this.publish = value; }
    public SiteRoleType getSiteRole() { return siteRole; }
    public void setSiteRole(SiteRoleType value) { this.siteRole = value; }
    public Boolean getSuppressGettingStarted() { return suppressGettingStarted; }
    public void setSuppressGettingStarted(Boolean value) { this.suppressGettingStarted = value; }
}
