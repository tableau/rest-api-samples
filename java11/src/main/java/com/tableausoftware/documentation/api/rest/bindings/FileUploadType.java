// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlAttribute;
import jakarta.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "fileUploadType")
public class FileUploadType {

    @XmlAttribute(name = "uploadSessionId", required = true)
    protected String uploadSessionId;
    @XmlAttribute(name = "fileSize")
    protected String fileSize;
    @XmlAttribute(name = "maxFileChunkCount")
    protected Integer maxFileChunkCount;

    public String getUploadSessionId() { return uploadSessionId; }
    public void setUploadSessionId(String value) { this.uploadSessionId = value; }
    public String getFileSize() { return fileSize; }
    public void setFileSize(String value) { this.fileSize = value; }
    public Integer getMaxFileChunkCount() { return maxFileChunkCount; }
    public void setMaxFileChunkCount(Integer value) { this.maxFileChunkCount = value; }
}
