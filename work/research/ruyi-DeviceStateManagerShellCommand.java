package com.android.server.devicestate;

import android.hardware.devicestate.DeviceState;
import android.hardware.devicestate.DeviceStateManager;
import android.hardware.devicestate.DeviceStateRequest;
import android.os.Binder;
import android.os.ShellCommand;
import java.io.PrintWriter;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.Executor;
import java.util.function.Function;
import java.util.stream.Collectors;

/* JADX INFO: loaded from: classes2.dex */
public class DeviceStateManagerShellCommand extends ShellCommand {
    private static DeviceStateRequest sLastBaseStateRequest;
    private static DeviceStateRequest sLastRequest;
    private final DeviceStateManager mClient;
    private final DeviceStateManagerService mService;

    public DeviceStateManagerShellCommand(DeviceStateManagerService service) {
        this.mService = service;
        this.mClient = (DeviceStateManager) service.getContext().getSystemService(DeviceStateManager.class);
    }

    /* JADX WARN: Can't fix incorrect switch cases order, some code will duplicate */
    /* JADX WARN: Code duplicated, block: B:23:0x0049  */
    public int onCommand(String cmd) {
        byte b;
        if (cmd == null) {
            return handleDefaultCommands(cmd);
        }
        PrintWriter pw = getOutPrintWriter();
        switch (cmd.hashCode()) {
            case -1906524523:
                if (!cmd.equals("base-state")) {
                    b = -1;
                } else {
                    b = 1;
                }
                break;
            case -1422060175:
                if (!cmd.equals("print-state")) {
                    b = -1;
                } else {
                    b = 2;
                }
                break;
            case -1134192350:
                if (!cmd.equals("print-states")) {
                    b = -1;
                } else {
                    b = 3;
                }
                break;
            case -295380803:
                if (!cmd.equals("print-states-simple")) {
                    b = -1;
                } else {
                    b = 4;
                }
                break;
            case 109757585:
                if (!cmd.equals("state")) {
                    b = -1;
                } else {
                    b = 0;
                }
                break;
            default:
                b = -1;
                break;
        }
        switch (b) {
            case 0:
                return runState(pw);
            case 1:
                return runBaseState(pw);
            case 2:
                return runPrintState(pw);
            case 3:
                return runPrintStates(pw);
            case 4:
                return runPrintStatesSimple(pw);
            default:
                return handleDefaultCommands(cmd);
        }
    }

    private void printAllStates(PrintWriter pw) {
        Optional<DeviceState> committedState = this.mService.getCommittedState();
        Optional<DeviceState> baseState = this.mService.getBaseState();
        Optional<DeviceState> overrideState = this.mService.getOverrideState();
        pw.println("Committed state: " + toString(committedState));
        if (overrideState.isPresent()) {
            pw.println("----------------------");
            pw.println("Base state: " + toString(baseState));
            pw.println("Override state: " + overrideState.get());
        }
    }

    private int runState(PrintWriter pw) {
        String nextArg = getNextArg();
        if (nextArg == null) {
            printAllStates(pw);
            return 0;
        }
        long callingIdentity = Binder.clearCallingIdentity();
        try {
            if (!"reset".equals(nextArg)) {
                int requestedState = Integer.parseInt(nextArg);
                DeviceStateRequest request = DeviceStateRequest.newBuilder(requestedState).build();
                this.mClient.requestState(request, (Executor) null, (DeviceStateRequest.Callback) null);
                sLastRequest = request;
            } else if (sLastRequest != null) {
                this.mClient.cancelStateRequest();
                sLastRequest = null;
            }
            return 0;
        } catch (NumberFormatException e) {
            getErrPrintWriter().println("Error: requested state should be an integer");
            return -1;
        } catch (IllegalArgumentException e2) {
            getErrPrintWriter().println("Error: " + e2.getMessage());
            getErrPrintWriter().println("-------------------");
            getErrPrintWriter().println("Run:");
            getErrPrintWriter().println("");
            getErrPrintWriter().println("    print-states");
            getErrPrintWriter().println("");
            getErrPrintWriter().println("to get the list of currently supported device states");
            return -1;
        } finally {
            Binder.restoreCallingIdentity(callingIdentity);
        }
    }

    private int runBaseState(PrintWriter pw) {
        String nextArg = getNextArg();
        if (nextArg == null) {
            printAllStates(pw);
            return 0;
        }
        long callingIdentity = Binder.clearCallingIdentity();
        try {
            if (!"reset".equals(nextArg)) {
                int requestedState = Integer.parseInt(nextArg);
                DeviceStateRequest request = DeviceStateRequest.newBuilder(requestedState).build();
                this.mClient.requestBaseStateOverride(request, (Executor) null, (DeviceStateRequest.Callback) null);
                sLastBaseStateRequest = request;
            } else if (sLastBaseStateRequest != null) {
                this.mClient.cancelBaseStateOverride();
                sLastBaseStateRequest = null;
            }
            return 0;
        } catch (NumberFormatException e) {
            getErrPrintWriter().println("Error: requested state should be an integer");
            return -1;
        } catch (IllegalArgumentException e2) {
            getErrPrintWriter().println("Error: " + e2.getMessage());
            getErrPrintWriter().println("-------------------");
            getErrPrintWriter().println("Run:");
            getErrPrintWriter().println("");
            getErrPrintWriter().println("    print-states");
            getErrPrintWriter().println("");
            getErrPrintWriter().println("to get the list of currently supported device states");
            return -1;
        } finally {
            Binder.restoreCallingIdentity(callingIdentity);
        }
    }

    private int runPrintState(PrintWriter pw) {
        Optional<DeviceState> deviceState = this.mService.getCommittedState();
        if (deviceState.isPresent()) {
            pw.println(deviceState.get().getIdentifier());
            return 0;
        }
        getErrPrintWriter().println("Error: device state not available.");
        return 1;
    }

    private int runPrintStates(PrintWriter pw) {
        List<DeviceState> states = this.mService.getSupportedStates();
        pw.print("Supported states: [\n");
        for (int i = 0; i < states.size(); i++) {
            pw.print("  " + states.get(i) + ",\n");
        }
        pw.println("]");
        return 0;
    }

    private int runPrintStatesSimple(PrintWriter pw) {
        pw.print((String) this.mService.getSupportedStates().stream().map(new Function() { // from class: com.android.server.devicestate.DeviceStateManagerShellCommand$$ExternalSyntheticLambda0
            @Override // java.util.function.Function
            public final Object apply(Object obj) {
                return Integer.valueOf(((DeviceState) obj).getIdentifier());
            }
        }).map(new Function() { // from class: com.android.server.devicestate.DeviceStateManagerShellCommand$$ExternalSyntheticLambda1
            @Override // java.util.function.Function
            public final Object apply(Object obj) {
                return ((Integer) obj).toString();
            }
        }).collect(Collectors.joining(",")));
        return 0;
    }

    public void onHelp() {
        PrintWriter pw = getOutPrintWriter();
        pw.println("Device state manager (device_state) commands:");
        pw.println("  help");
        pw.println("    Print this help text.");
        pw.println("  state [reset|OVERRIDE_DEVICE_STATE]");
        pw.println("    Return or override device state.");
        pw.println("  print-state");
        pw.println("    Return the current device state.");
        pw.println("  print-states");
        pw.println("    Return list of currently supported device states.");
        pw.println("  print-states-simple");
        pw.println("    Return the currently supported device states in comma separated format.");
    }

    private static String toString(Optional<DeviceState> state) {
        return state.isPresent() ? state.get().toString() : "(none)";
    }
}
