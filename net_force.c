#include <stdio.h>
#include "vpi_user.h"

/**
 * This file contains C-language functions that interact with the VCS simulation
 * via the VCS interface. We use this to force and release the values on nets
 * given the names in string format.
 * 
 * See the vcs manual for details:
 * https://users.ece.utexas.edu/~patt/10s.382N/handouts/vcs.pdf
 * 
 * VPI: 17-29
 * Force and Release: 22-28/22-29 
 * 
 * TODO: compile into shared library (add makefile rule)
 */

// given string name for net, force that net to have specified value
void force_net_by_name(const char *netname, int value) {
    vpiHandle net_h = vpi_handle_by_name((PLI_BYTE8 *)netname, NULL);
    if (!net_h) {
        vpi_printf("Error: (force) net '%s' not found.\n", netname);
        return;
    }

    s_vpi_value val_s;
    val_s.format = vpiIntVal;
    val_s.value.integer = value;
    vpi_put_value(net_h, &val_s, 0, vpiForceFlag);
}

void release_net_by_name(const char *netname) {
    vpiHandle net_h = vpi_handle_by_name((PLI_BYTE8 *)netname, NULL);
    if (!net_h) {
        vpi_printf("Error: (release) net '%s' not found.\n", netname);
        return;
    }

    s_vpi_value val_s;
    val_s.format = vpiIntVal;
    val_s.value.integer = 0; // this is ignored 
    vpi_put_value(net_h, &val_s, 0, vpiReleaseFlag);
}

int get_net_value_by_name(const char *netname) {
    vpiHandle net_h = vpi_handle_by_name((PLI_BYTE8 *)netname, NULL);
    if (!net_h) {
        vpi_printf("Error: (get_value) net '%s' not found.\n", netname);
        return -1;
    }

    s_vpi_value value_s;
    value_s.format = vpiIntVal;  // or another format such as vpiBinStrVal, depending on your needs

    vpi_get_value(net_h, &value_s);
    return value_s.value.integer;
}

// DPI wrappers
extern int force_net_by_name_dpi(const char *netname, int value) {
    force_net_by_name(netname, value);
    return 0;
}

extern int release_net_by_name_dpi(const char *netname) {
    release_net_by_name(netname);
    return 0;
}

extern int get_net_value_by_name_dpi(const char *netname) {
    return get_net_value_by_name(netname);
}
