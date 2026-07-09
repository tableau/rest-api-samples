// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import java.util.ArrayList;
import java.util.List;
import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "permissionsType", propOrder = { "workbook", "granteeCapabilities", "parent" })
public class PermissionsType {

    protected ParentType parent;
    protected WorkbookType workbook;
    protected List<GranteeCapabilitiesType> granteeCapabilities;

    public ParentType getParent() { return parent; }
    public void setParent(ParentType value) { this.parent = value; }
    public WorkbookType getWorkbook() { return workbook; }
    public void setWorkbook(WorkbookType value) { this.workbook = value; }

    public List<GranteeCapabilitiesType> getGranteeCapabilities() {
        if (granteeCapabilities == null) {
            granteeCapabilities = new ArrayList<>();
        }
        return this.granteeCapabilities;
    }
}
