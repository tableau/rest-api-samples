// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import java.math.BigInteger;
import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlAttribute;
import jakarta.xml.bind.annotation.XmlSchemaType;
import jakarta.xml.bind.annotation.XmlType;
import javax.xml.datatype.XMLGregorianCalendar;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "workbookType", propOrder = { "owner", "project", "site", "tags", "views" })
public class WorkbookType {

    protected UserType owner;
    protected ProjectType project;
    protected SiteType site;
    protected TagListType tags;
    protected ViewListType views;
    @XmlAttribute(name = "contentUrl")
    protected String contentUrl;
    @XmlAttribute(name = "createdAt")
    @XmlSchemaType(name = "dateTime")
    protected XMLGregorianCalendar createdAt;
    @XmlAttribute(name = "defaultViewId")
    protected String defaultViewId;
    @XmlAttribute(name = "description")
    protected String description;
    @XmlAttribute(name = "encryptExtracts")
    protected String encryptExtracts;
    @XmlAttribute(name = "hasExtracts")
    protected Boolean hasExtracts;
    @XmlAttribute(name = "id")
    protected String id;
    @XmlAttribute(name = "lastPublishedAt")
    @XmlSchemaType(name = "dateTime")
    protected XMLGregorianCalendar lastPublishedAt;
    @XmlAttribute(name = "name")
    protected String name;
    @XmlAttribute(name = "primaryContentUrl")
    protected String primaryContentUrl;
    @XmlAttribute(name = "recentlyViewed")
    protected Boolean recentlyViewed;
    @XmlAttribute(name = "shareDescription")
    protected String shareDescription;
    @XmlAttribute(name = "sheetCount")
    @XmlSchemaType(name = "nonNegativeInteger")
    protected BigInteger sheetCount;
    @XmlAttribute(name = "showTabs")
    protected String showTabs;
    @XmlAttribute(name = "size")
    @XmlSchemaType(name = "nonNegativeInteger")
    protected BigInteger size;
    @XmlAttribute(name = "thumbnailsGroupId")
    protected String thumbnailsGroupId;
    @XmlAttribute(name = "thumbnailsUserId")
    protected String thumbnailsUserId;
    @XmlAttribute(name = "updatedAt")
    @XmlSchemaType(name = "dateTime")
    protected XMLGregorianCalendar updatedAt;
    @XmlAttribute(name = "webpageUrl")
    protected String webpageUrl;

    public UserType getOwner() { return owner; }
    public void setOwner(UserType value) { this.owner = value; }
    public ProjectType getProject() { return project; }
    public void setProject(ProjectType value) { this.project = value; }
    public SiteType getSite() { return site; }
    public void setSite(SiteType value) { this.site = value; }
    public TagListType getTags() { return tags; }
    public void setTags(TagListType value) { this.tags = value; }
    public ViewListType getViews() { return views; }
    public void setViews(ViewListType value) { this.views = value; }
    public String getContentUrl() { return contentUrl; }
    public void setContentUrl(String value) { this.contentUrl = value; }
    public XMLGregorianCalendar getCreatedAt() { return createdAt; }
    public void setCreatedAt(XMLGregorianCalendar value) { this.createdAt = value; }
    public String getDefaultViewId() { return defaultViewId; }
    public void setDefaultViewId(String value) { this.defaultViewId = value; }
    public String getDescription() { return description; }
    public void setDescription(String value) { this.description = value; }
    public String getEncryptExtracts() { return encryptExtracts; }
    public void setEncryptExtracts(String value) { this.encryptExtracts = value; }
    public Boolean getHasExtracts() { return hasExtracts; }
    public void setHasExtracts(Boolean value) { this.hasExtracts = value; }
    public String getId() { return id; }
    public void setId(String value) { this.id = value; }
    public XMLGregorianCalendar getLastPublishedAt() { return lastPublishedAt; }
    public void setLastPublishedAt(XMLGregorianCalendar value) { this.lastPublishedAt = value; }
    public String getName() { return name; }
    public void setName(String value) { this.name = value; }
    public String getPrimaryContentUrl() { return primaryContentUrl; }
    public void setPrimaryContentUrl(String value) { this.primaryContentUrl = value; }
    public Boolean getRecentlyViewed() { return recentlyViewed; }
    public void setRecentlyViewed(Boolean value) { this.recentlyViewed = value; }
    public String getShareDescription() { return shareDescription; }
    public void setShareDescription(String value) { this.shareDescription = value; }
    public BigInteger getSheetCount() { return sheetCount; }
    public void setSheetCount(BigInteger value) { this.sheetCount = value; }
    public String getShowTabs() { return showTabs; }
    public void setShowTabs(String value) { this.showTabs = value; }
    public BigInteger getSize() { return size; }
    public void setSize(BigInteger value) { this.size = value; }
    public String getThumbnailsGroupId() { return thumbnailsGroupId; }
    public void setThumbnailsGroupId(String value) { this.thumbnailsGroupId = value; }
    public String getThumbnailsUserId() { return thumbnailsUserId; }
    public void setThumbnailsUserId(String value) { this.thumbnailsUserId = value; }
    public XMLGregorianCalendar getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(XMLGregorianCalendar value) { this.updatedAt = value; }
    public String getWebpageUrl() { return webpageUrl; }
    public void setWebpageUrl(String value) { this.webpageUrl = value; }
}
