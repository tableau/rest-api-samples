// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlAttribute;
import jakarta.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "capabilityType")
public class CapabilityType {

    @XmlAttribute(name = "name", required = true)
    protected String name;
    @XmlAttribute(name = "mode", required = true)
    protected String mode;

    public String getName() { return name; }
    public void setName(String value) { this.name = value; }
    public String getMode() { return mode; }
    public void setMode(String value) { this.mode = value; }
}
