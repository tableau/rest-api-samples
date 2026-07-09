// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlAttribute;
import jakarta.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "tagType")
public class TagType {

    @XmlAttribute(name = "label", required = true)
    protected String label;

    public String getLabel() { return label; }
    public void setLabel(String value) { this.label = value; }
}
