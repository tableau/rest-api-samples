// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlRootElement;
import jakarta.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "", propOrder = {
    "pagination",
    "groups",
    "projects",
    "sites",
    "workbooks",
    "credentials",
    "error",
    "fileUpload",
    "group",
    "permissions",
    "workbook"
})
@XmlRootElement(name = "tsResponse")
public class TsResponse {

    protected PaginationType pagination;
    protected GroupListType groups;
    protected ProjectListType projects;
    protected SiteListType sites;
    protected WorkbookListType workbooks;
    protected TableauCredentialsType credentials;
    protected ErrorType error;
    protected FileUploadType fileUpload;
    protected GroupType group;
    protected PermissionsType permissions;
    protected WorkbookType workbook;

    public PaginationType getPagination() { return pagination; }
    public void setPagination(PaginationType value) { this.pagination = value; }
    public GroupListType getGroups() { return groups; }
    public void setGroups(GroupListType value) { this.groups = value; }
    public ProjectListType getProjects() { return projects; }
    public void setProjects(ProjectListType value) { this.projects = value; }
    public SiteListType getSites() { return sites; }
    public void setSites(SiteListType value) { this.sites = value; }
    public WorkbookListType getWorkbooks() { return workbooks; }
    public void setWorkbooks(WorkbookListType value) { this.workbooks = value; }
    public TableauCredentialsType getCredentials() { return credentials; }
    public void setCredentials(TableauCredentialsType value) { this.credentials = value; }
    public ErrorType getError() { return error; }
    public void setError(ErrorType value) { this.error = value; }
    public FileUploadType getFileUpload() { return fileUpload; }
    public void setFileUpload(FileUploadType value) { this.fileUpload = value; }
    public GroupType getGroup() { return group; }
    public void setGroup(GroupType value) { this.group = value; }
    public PermissionsType getPermissions() { return permissions; }
    public void setPermissions(PermissionsType value) { this.permissions = value; }
    public WorkbookType getWorkbook() { return workbook; }
    public void setWorkbook(WorkbookType value) { this.workbook = value; }
}
