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
@XmlType(name = "viewType", propOrder = { "usage" })
public class ViewType {

    protected ViewType.Usage usage;
    @XmlAttribute(name = "id")
    protected String id;
    @XmlAttribute(name = "name")
    protected String name;
    @XmlAttribute(name = "contentUrl")
    protected String contentUrl;

    public ViewType.Usage getUsage() { return usage; }
    public void setUsage(ViewType.Usage value) { this.usage = value; }
    public String getId() { return id; }
    public void setId(String value) { this.id = value; }
    public String getName() { return name; }
    public void setName(String value) { this.name = value; }
    public String getContentUrl() { return contentUrl; }
    public void setContentUrl(String value) { this.contentUrl = value; }

    @XmlAccessorType(XmlAccessType.FIELD)
    @XmlType(name = "")
    public static class Usage {

        @XmlAttribute(name = "totalViewCount", required = true)
        @XmlSchemaType(name = "nonNegativeInteger")
        protected BigInteger totalViewCount;

        public BigInteger getTotalViewCount() { return totalViewCount; }
        public void setTotalViewCount(BigInteger value) { this.totalViewCount = value; }
    }
}
