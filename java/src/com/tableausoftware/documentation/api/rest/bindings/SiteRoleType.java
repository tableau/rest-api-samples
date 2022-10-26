//
// This file was generated by the JavaTM Architecture for XML Binding(JAXB) Reference Implementation, v2.2.8-b130911.1802
// See <a href="http://java.sun.com/xml/jaxb">http://java.sun.com/xml/jaxb</a>
// Any modifications to this file will be lost upon recompilation of the source schema.
// Generated on: 2015.09.21 at 01:55:40 PM PDT
//

package com.tableausoftware.documentation.api.rest.bindings;

import javax.xml.bind.annotation.XmlEnum;
import javax.xml.bind.annotation.XmlEnumValue;
import javax.xml.bind.annotation.XmlType;

/**
 * <p>
 * Java class for siteRoleType.
 *
 * <p>
 * The following schema fragment specifies the expected content contained within this class.
 * <p>
 *
 * <pre>
 * &lt;simpleType name="siteRoleType">
 *   &lt;restriction base="{http://www.w3.org/2001/XMLSchema}string">
 *     &lt;enumeration value="Guest"/>
 *     &lt;enumeration value="Creator"/>
 *     &lt;enumeration value="Explorer"/>
 *     &lt;enumeration value="ExplorerCanPublish"/>
 *     &lt;enumeration value="ReadOnly"/>
 *     &lt;enumeration value="Interactor"/>
 *     &lt;enumeration value="Publisher"/>
 *     &lt;enumeration value="ServerAdministrator"/>
 *     &lt;enumeration value="SiteAdministrator"/>
 *     &lt;enumeration value="SiteAdministratorCreator"/>
 *     &lt;enumeration value="SiteAdministratorExplorer"/>
 *     &lt;enumeration value="Unlicensed"/>
 *     &lt;enumeration value="UnlicensedWithPublish"/>
 *     &lt;enumeration value="Viewer"/>
 *     &lt;enumeration value="ViewerWithPublish"/>
 *   &lt;/restriction>
 * &lt;/simpleType>
 * </pre>
 *
 */
@XmlType(name = "siteRoleType")
@XmlEnum
public enum SiteRoleType {

    @XmlEnumValue("Guest")
    GUEST("Guest"),
    @XmlEnumValue("Creator")
    CREATOR("Creator"),
    @XmlEnumValue("Explorer")
    EXPLORER("Explorer"),
    @XmlEnumValue("ExplorerCanPublish")
    EXPLORERCANPUBLISH("ExplorerCanPublish"),
    @XmlEnumValue("ReadOnly")
    READONLY("ReadOnly"),
    @XmlEnumValue("Interactor")
    INTERACTOR("Interactor"),
    @XmlEnumValue("Publisher")
    PUBLISHER("Publisher"),
    @XmlEnumValue("ServerAdministrator")
    SERVER_ADMINISTRATOR("ServerAdministrator"),
    @XmlEnumValue("SiteAdministrator")
    SITE_ADMINISTRATOR("SiteAdministrator"),
    @XmlEnumValue("SiteAdministratorCreator")
    SITE_ADMINISTRATOR_CREATOR("SiteAdministratorCreator"),
    @XmlEnumValue("SiteAdministratorExplorer")
    SITE_ADMINISTRATOR_EXPLORER("SiteAdministratorExplorer"),
    @XmlEnumValue("Unlicensed")
    UNLICENSED("Unlicensed"),
    @XmlEnumValue("UnlicensedWithPublish")
    UNLICENSED_WITH_PUBLISH("UnlicensedWithPublish"),
    @XmlEnumValue("Viewer")
    VIEWER("Viewer"),
    @XmlEnumValue("ViewerWithPublish")
    VIEWER_WITH_PUBLISH("ViewerWithPublish");

    private final String value;

    SiteRoleType(String v) {
        value = v;
    }

    public String value() {
        return value;
    }

    public static SiteRoleType fromValue(String v) {
        for (SiteRoleType c : SiteRoleType.values()) {
            if (c.value.equals(v)) {
                return c;
            }
        }
        throw new IllegalArgumentException(v);
    }

}
