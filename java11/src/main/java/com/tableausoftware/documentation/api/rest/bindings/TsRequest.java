// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlRootElement;
import jakarta.xml.bind.annotation.XmlType;

/**
 * Partial binding for Demo.java request payloads. The full schema models tsRequest
 * as an xs:choice (at most one child element per request); this binding uses a
 * sequence so that JAXB can represent all variants in a single class. Only set
 * one field per instance to remain schema-compliant.
 */
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "", propOrder = { "credentials", "group", "permissions", "workbook" })
@XmlRootElement(name = "tsRequest")
public class TsRequest {

    protected TableauCredentialsType credentials;
    protected GroupType group;
    protected PermissionsType permissions;
    protected WorkbookType workbook;

    public TableauCredentialsType getCredentials() { return credentials; }
    public void setCredentials(TableauCredentialsType value) { this.credentials = value; }
    public GroupType getGroup() { return group; }
    public void setGroup(GroupType value) { this.group = value; }
    public PermissionsType getPermissions() { return permissions; }
    public void setPermissions(PermissionsType value) { this.permissions = value; }
    public WorkbookType getWorkbook() { return workbook; }
    public void setWorkbook(WorkbookType value) { this.workbook = value; }
}
