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
@XmlType(name = "paginationType")
public class PaginationType {

    @XmlAttribute(name = "pageNumber", required = true)
    @XmlSchemaType(name = "positiveInteger")
    protected BigInteger pageNumber;
    @XmlAttribute(name = "pageSize", required = true)
    @XmlSchemaType(name = "nonNegativeInteger")
    protected BigInteger pageSize;
    @XmlAttribute(name = "totalAvailable", required = true)
    @XmlSchemaType(name = "nonNegativeInteger")
    protected BigInteger totalAvailable;

    public BigInteger getPageNumber() { return pageNumber; }
    public void setPageNumber(BigInteger value) { this.pageNumber = value; }
    public BigInteger getPageSize() { return pageSize; }
    public void setPageSize(BigInteger value) { this.pageSize = value; }
    public BigInteger getTotalAvailable() { return totalAvailable; }
    public void setTotalAvailable(BigInteger value) { this.totalAvailable = value; }
}
