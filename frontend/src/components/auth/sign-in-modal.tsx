"use client";

import { useState } from "react";
import { LogIn } from "lucide-react";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/lib/hooks";

interface SignInModalProps {
  open: boolean;
  onClose: () => void;
  onSwitchToSignUp: () => void;
}

/**
 * Sign In Modal component matching GIM.pen design (lNFWv).
 */
export function SignInModal({ open, onClose, onSwitchToSignUp }: SignInModalProps) {
  const [gimId, setGimId] = useState("");
  const { signIn, isLoading, error, isValidGimId } = useAuth();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isValidGimId(gimId)) {
      signIn(gimId, {
        onSuccess: () => {
          onClose();
          setGimId("");
        },
      });
    }
  };

  const isValid = gimId.length > 0 && isValidGimId(gimId);

  return (
    <Modal open={open} onClose={onClose}>
      <ModalHeader onClose={onClose}>
        <ModalTitle>Welcome Back</ModalTitle>
      </ModalHeader>

      <ModalContent>
        <Tabs defaultValue="signin">
          <TabsList className="w-full">
            <TabsTrigger value="signin" className="flex-1">Sign In</TabsTrigger>
            <TabsTrigger
              value="signup"
              className="flex-1"
              onClick={onSwitchToSignUp}
            >
              Sign Up
            </TabsTrigger>
          </TabsList>
        </Tabs>

        <p className="text-sm text-text-secondary">
          Enter your GIM ID to access your profile and contributions.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="flex flex-col gap-2">
            <label htmlFor="gimId" className="text-sm font-medium text-text-primary">
              GIM ID
            </label>
            <Input
              id="gimId"
              type="text"
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              value={gimId}
              onChange={(e) => setGimId(e.target.value)}
              error={gimId.length > 0 && !isValid}
              disabled={isLoading}
            />
            {gimId.length > 0 && !isValid && (
              <p className="text-xs text-destructive">
                Please enter a valid UUID format
              </p>
            )}
            {error && <p className="text-xs text-destructive">{error}</p>}
          </div>

          <ModalFooter>
            <Button
              type="submit"
              className="w-full"
              disabled={!isValid || isLoading}
            >
              <LogIn className="h-4 w-4" />
              {isLoading ? "Signing in..." : "Sign In"}
            </Button>
            <p className="text-center text-xs text-text-muted">
              Don&apos;t have an ID?{" "}
              <button
                type="button"
                onClick={onSwitchToSignUp}
                className="text-primary underline hover:no-underline"
              >
                Create one
              </button>
            </p>
          </ModalFooter>
        </form>
      </ModalContent>
    </Modal>
  );
}
