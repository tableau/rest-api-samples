// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import java.util.ArrayList;
import java.util.List;
import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlType;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "workbookListType", propOrder = { "workbook" })
public class WorkbookListType {

    protected List<WorkbookType> workbook;

    public List<WorkbookType> getWorkbook() {
        if (workbook == null) {
            workbook = new ArrayList<>();
        }
        return this.workbook;
    }
}
