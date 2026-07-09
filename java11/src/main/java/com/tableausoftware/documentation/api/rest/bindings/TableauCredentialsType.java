// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlAttribute;
import jakarta.xml.bind.annotation.XmlElement;
import jakarta.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "tableauCredentialsType", propOrder = { "site", "user" })
public class TableauCredentialsType {

    @XmlElement(required = true)
    protected SiteType site;
    protected UserType user;
    @XmlAttribute(name = "estimatedTimeToExpiration")
    protected String estimatedTimeToExpiration;
    @XmlAttribute(name = "isUat")
    protected Boolean isUat;
    @XmlAttribute(name = "jwt")
    protected String jwt;
    @XmlAttribute(name = "name")
    protected String name;
    @XmlAttribute(name = "password")
    protected String password;
    @XmlAttribute(name = "personalAccessTokenName")
    protected String personalAccessTokenName;
    @XmlAttribute(name = "personalAccessTokenSecret")
    protected String personalAccessTokenSecret;
    @XmlAttribute(name = "token")
    protected String token;

    public SiteType getSite() { return site; }
    public void setSite(SiteType value) { this.site = value; }
    public UserType getUser() { return user; }
    public void setUser(UserType value) { this.user = value; }
    public String getEstimatedTimeToExpiration() { return estimatedTimeToExpiration; }
    public void setEstimatedTimeToExpiration(String value) { this.estimatedTimeToExpiration = value; }
    public Boolean getIsUat() { return isUat; }
    public void setIsUat(Boolean value) { this.isUat = value; }
    public String getJwt() { return jwt; }
    public void setJwt(String value) { this.jwt = value; }
    public String getName() { return name; }
    public void setName(String value) { this.name = value; }
    public String getPassword() { return password; }
    public void setPassword(String value) { this.password = value; }
    public String getPersonalAccessTokenName() { return personalAccessTokenName; }
    public void setPersonalAccessTokenName(String value) { this.personalAccessTokenName = value; }
    public String getPersonalAccessTokenSecret() { return personalAccessTokenSecret; }
    public void setPersonalAccessTokenSecret(String value) { this.personalAccessTokenSecret = value; }
    public String getToken() { return token; }
    public void setToken(String value) { this.token = value; }
}
