// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import java.math.BigInteger;
import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlAttribute;
import jakarta.xml.bind.annotation.XmlElement;
import jakarta.xml.bind.annotation.XmlSchemaType;
import jakarta.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "errorType", propOrder = { "callstack", "detail", "summary" })
public class ErrorType {

    @XmlElement
    protected String callstack;
    @XmlElement(required = true)
    protected String detail;
    @XmlElement(required = true)
    protected String summary;
    @XmlAttribute(name = "code", required = true)
    @XmlSchemaType(name = "positiveInteger")
    protected BigInteger code;

    public String getCallstack() { return callstack; }
    public void setCallstack(String value) { this.callstack = value; }
    public String getDetail() { return detail; }
    public void setDetail(String value) { this.detail = value; }
    public String getSummary() { return summary; }
    public void setSummary(String value) { this.summary = value; }
    public BigInteger getCode() { return code; }
    public void setCode(BigInteger value) { this.code = value; }
}
